# Native standalone Ethernet PVLAN support for dcnm_interface (parent template int_pvlan_host).
#
# Pure helpers only: no HTTP path, no transport and no AnsibleModule. The module owns I/O and
# calls these for four things:
#
#   1. strict validation of the RAW playbook profile, before Ansible coercion or defaults;
#   2. the native list wire form (JSON-string wrappers of scalar P_VLAN/S_VLAN rows);
#   3. per-state reconciliation of WANT against an authoritative HAVE, producing the FULL
#      outgoing nvPair set, the reported diff and every reason to refuse before a write;
#   4. a CLI transition model and the fresh-pending validator used immediately before deploy.
#
# The CLI model is derived from the installed int_pvlan_host template's add() renderer
# (content sha256 5c227412569ff80d53b830d1e509a9fb1a68feb8683dfabfa2087d9bdb1eace3) and from
# measured pendings. Anything it does not model is refused, never waved through.
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import ast
import json
import re

# The REGISTRY_BINDING companions are owned by the packaged binding table; this
# helper only wires them into the PVLAN routes (allowlist, raw validation, full set, withdrawal, CLI model).
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    registered_profile_keys,
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GIE_WITHDRAW_INAPPLICABLE,
    GIE_WITHDRAW_NONE,
    GIE_WITHDRAW_RESET,
    GieBindingError,
    gie_contribute_nvpairs,
    gie_validate_binding_value,
    gie_withdrawal_action,
)

PVLAN_POLICY = "int_pvlan_host"
TRUNK_HOST_POLICY = "int_trunk_host"

MODE_HOST = "host"
MODE_PROMISCUOUS = "promiscuous"
MODE_TRUNK_PROMISCUOUS = "trunk promiscuous"
MODE_TRUNK_SECONDARY = "trunk secondary"
PVLAN_MODES = (MODE_HOST, MODE_PROMISCUOUS, MODE_TRUNK_PROMISCUOUS, MODE_TRUNK_SECONDARY)
TRUNK_MODES = (MODE_TRUNK_PROMISCUOUS, MODE_TRUNK_SECONDARY)
ASSOCIATION_MODES = (MODE_HOST, MODE_TRUNK_SECONDARY)
MAPPING_MODES = (MODE_PROMISCUOUS, MODE_TRUNK_PROMISCUOUS)

ASSOCIATION_LIST = "ASSOCIATION_LIST"
MAPPING_LIST = "MAPPING_LIST"
NATIVE_VLAN = "PVLAN_NATIVE_VLAN"
ALLOWED_VLANS = "PVLAN_ALLOWED_VLANS"

# public key, nvPair, kind, template default (wire form)
COMPANIONS = (
    ("description", "DESC", "str", ""),
    ("admin_state", "ADMIN_STATE", "bool", "true"),
    ("bpdu_guard", "BPDUGUARD_ENABLED", "bpdu", "no"),
    ("port_type_fast", "PORTTYPE_FAST_ENABLED", "bool", "true"),
    ("mtu", "MTU", "mtu", "jumbo"),
    ("speed", "SPEED", "speed", "Auto"),
    ("enable_cdp", "CDP_ENABLE", "bool", "true"),
    ("orphan_port", "ENABLE_ORPHAN_PORT", "bool", "false"),
    ("duplex", "PORT_DUPLEX_MODE", "duplex", "auto"),
    ("enable_pfc", "ENABLE_PFC", "bool", "false"),
    ("enable_qos", "ENABLE_QOS", "bool", "false"),
    ("qos_policy", "QOS_POLICY", "str", ""),
    ("queuing_policy", "QUEUING_POLICY", "str", ""),
    ("cmds", "CONF", "conf", ""),
)
COMPANION_BY_KEY = dict((c[0], c) for c in COMPANIONS)
PRESERVE_ALWAYS = ("lldpTransmit", "lldpReceive")
PRESERVE_SAME_POLICY = ("PTP",)
BOOKKEEPING = ("SERIAL_NUMBER", "FABRIC_NAME", "POLICY_ID", "PRIORITY", "POLICY_DESC", "MARK_DELETED")
NATIVE_NVPAIRS = ("PVLAN_MODE", ASSOCIATION_LIST, MAPPING_LIST, NATIVE_VLAN, ALLOWED_VLANS)
KNOWN_HAVE_NVPAIRS = frozenset(NATIVE_NVPAIRS + tuple(c[1] for c in COMPANIONS) + PRESERVE_ALWAYS + PRESERVE_SAME_POLICY + BOOKKEEPING + ("INTF_NAME",))

# The registry companions of int_pvlan_host (lldpTransmit, lldpReceive). Derived from the
# packaged table so the allowlist cannot drift from the bindings it accepts.
REGISTRY_KEYS = frozenset(registered_profile_keys(PVLAN_POLICY))
PROFILE_KEYS = frozenset(("mode", "pvlan_mode", "pvlan_association", "pvlan_mapping", "native_vlan", "allowed_vlans") + tuple(c[0] for c in COMPANIONS)) \
    | REGISTRY_KEYS
# Keys dcnm_intf_copy_config injects into its profile copy; never user input.
INJECTED_KEYS = frozenset(("fabric", "sno", "ifname", "policy"))

SPEED_VALUES = ("Auto", "10Mb", "100Mb", "1Gb", "2.5Gb", "5Gb", "10Gb", "25Gb", "40Gb", "50Gb", "100Gb", "200Gb", "400Gb", "800Gb")
# Input parity with the regular access/trunk profiles of this module: bpdu_guard takes a real boolean or the strings
# true/false/no in any letter case, speed takes any letter case of an exact SPEED_VALUES entry. Both are sent in the template's own
# spelling; "no" stays a third state and is never read as a boolean. Nothing else is accepted (no whitespace, no numbers, no aliases).
BPDU_VALUES = ("true", "false", "no")
_SPEED_BY_LOWER = dict((value.lower(), value) for value in SPEED_VALUES)


def canonical_native(kind, value):
    """The canonical wire value of a `bpdu` or `speed` companion, or None when `value` is not an accepted spelling.
    Any other kind is returned unchanged (its own validation applies)."""
    if kind == "bpdu":
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str) and value.lower() in BPDU_VALUES:
            return value.lower()
        return None
    if kind == "speed":
        if isinstance(value, str):
            return _SPEED_BY_LOWER.get(value.lower())
        return None
    return value


# RC1 (speed): the `speed <n>` keyword each template enum value renders through Util.mapEnumToSwitchSpeed (controller code, NOT captured).
# MEASURED for 1Gb only (regular int_trunk_host, NDFC 12.6.0.267: SPEED "1Gb" -> `speed 1000` in the controller's configuration); the
# other values follow the NX-OS convention of the speed in Mb/s (INFERRED). Auto renders no speed line (SPEED_STR_SWITCH_DEFAULT).
SPEED_CLI = {"10Mb": "10", "100Mb": "100", "1Gb": "1000", "2.5Gb": "2500", "5Gb": "5000", "10Gb": "10000", "25Gb": "25000",
             "40Gb": "40000", "50Gb": "50000", "100Gb": "100000", "200Gb": "200000", "400Gb": "400000", "800Gb": "800000"}
SPEED_CLI_MEASURED = frozenset(("1Gb",))
# RC1: the PVLAN templates add `no negotiate auto` after a speed line only when Util.getPortSpeedAutoNeg (device capability, controller
# code, NOT captured) answers "off"; they never render `negotiate auto`. The module cannot predict it, so the line is ADOPTED from the
# controller's own expected configuration, and only next to a non-Auto speed line (adopt_capability_lines).
# RC2 (L3): its WITHDRAWAL when the speed returns to Auto is INFERRED, not measured: the templates never render `negotiate auto`, so the
# pending is expected to carry `no speed <n>` and the positive form `negotiate auto` (the generic withdrawal of an owned `no X` line); a
# pending that differs is refused before any deploy.
NEGOTIATE_CAPABILITY_LINE = "no negotiate auto"
_SPEED_LINE = re.compile(r"^speed [0-9]+$")
# Freeform lines that would manage PVLAN or switchport mode outside the structured fields.
_CONF_FORBIDDEN = re.compile(r"private-vlan|^\s*(no\s+)?switchport\b", re.IGNORECASE)
_LINE_BREAK = re.compile(r"\r\n|\r|\n")


def cmds_lines(value):
    """PVLAN Ethernet `cmds` as a list of lines, or None if not accepted.

    A list of strings is the documented form. A text (how NAC renders freeform_config) is split into its lines; a text with a
    comma is refused, since the regular Ethernet path would split it there. List entries holding line breaks are split too."""
    if isinstance(value, str):
        if "," in value:
            return None
        lines = _LINE_BREAK.split(value) if value else []
        if lines and lines[-1] == "":
            lines.pop()
        return lines
    if isinstance(value, list) and all(isinstance(x, str) for x in value):
        out = []
        for entry in value:
            if _LINE_BREAK.search(entry):
                parts = _LINE_BREAK.split(entry)
                if parts and parts[-1] == "":
                    parts.pop()
                out.extend(parts)
            else:
                out.append(entry)
        return out
    return None


class PvlanError(ValueError):
    """Malformed input or controller state; the message never carries a secret."""


# ------------------------------------------------------------------ VLAN primitives
def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def vlan_id(value, field):
    if not _is_int(value):
        raise PvlanError("%s must be an integer VLAN ID, not %s" % (field, type(value).__name__))
    if not 1 <= value <= 4094:
        raise PvlanError("%s %d is outside 1-4094" % (field, value))
    return value


_VLAN_RANGE_RE = re.compile(r"^([1-9][0-9]{0,3})(?:-([1-9][0-9]{0,3}))?$")


def vlan_set(text, field):
    """Strict 'N', 'N-M' comma list -> sorted list of ints. Descending, overlapping or duplicate input is refused so duplicates
    cannot vanish in a set. SINGLETON-RANGE: a single-value inclusive range 'N-N' (what NaC's convert_ranges macro renders for
    from N / to N) is the VLAN N; it still counts toward the duplicate check ('2212,2212-2212' is refused)."""
    if not isinstance(text, str):
        raise PvlanError("%s must be a string" % field)
    out = []
    seen = set()
    parts = text.replace(" ", "").split(",")
    if text.strip() == "" or "" in parts:
        raise PvlanError("%s %r is not a VLAN list" % (field, text))
    for part in parts:
        m = _VLAN_RANGE_RE.match(part)
        if not m:
            raise PvlanError("%s %r is not a VLAN list" % (field, text))
        low = int(m.group(1))
        high = int(m.group(2)) if m.group(2) else low
        if m.group(2) and high < low:
            raise PvlanError("%s range %r is not ascending" % (field, part))
        for v in range(low, high + 1):
            if not 1 <= v <= 4094:
                raise PvlanError("%s %d is outside 1-4094" % (field, v))
            if v in seen:
                raise PvlanError("%s repeats VLAN %d" % (field, v))
            seen.add(v)
            out.append(v)
    return sorted(out)


_SINGLE_VALUE_RANGE_RE = re.compile(r"^\s*([1-9][0-9]{0,3})\s*-\s*([1-9][0-9]{0,3})\s*$")
# The raw PVLAN profile keys holding a VLAN list the module forwards or compares (pvlan_mapping rows: secondary_vlans).
SINGLE_VALUE_RANGE_KEYS = ("allowed_vlans", "peer1_allowed_vlans", "peer2_allowed_vlans")


def collapse_single_value_ranges(text):
    """SINGLETON-RANGE: each comma token that is a single-value range 'N-N' becomes 'N'; every other token is returned unchanged
    (a descending, malformed, out-of-range or duplicate value is left for the strict validator to refuse). A non-string is returned as
    is. 'N' is the form the controller stores and the module sends (int_pvlan_host measured '2301', not '2301-2301'), so N-N input
    produces the same payload and the same comparison as N."""
    if not isinstance(text, str):
        return text
    out = []
    for part in text.split(","):
        m = _SINGLE_VALUE_RANGE_RE.match(part)
        out.append(m.group(1) if m and m.group(1) == m.group(2) else part)
    return ",".join(out)


def normalize_single_value_ranges(profile):
    """SINGLETON-RANGE: collapse 'N-N' in the VLAN lists of a RAW `mode: pvlan` profile (allowed_vlans, peer1/peer2_allowed_vlans and
    every pvlan_mapping row's secondary_vlans), in place, before validation. Returns the changed keys (diagnostics). Nothing else is
    touched; values of the wrong type are left for the validator."""
    changed = []
    if not isinstance(profile, dict):
        return changed
    for key in SINGLE_VALUE_RANGE_KEYS:
        value = profile.get(key)
        new = collapse_single_value_ranges(value)
        if new != value:
            profile[key] = new
            changed.append(key)
    rows = profile.get("pvlan_mapping")
    if isinstance(rows, list):
        for index, row in enumerate(rows):
            if isinstance(row, dict) and isinstance(row.get("secondary_vlans"), str):
                new = collapse_single_value_ranges(row["secondary_vlans"])
                if new != row["secondary_vlans"]:
                    row["secondary_vlans"] = new
                    changed.append("pvlan_mapping[%d].secondary_vlans" % index)
    return changed


def _lenient_vlan_set(text):
    """Controller-side VLAN set (ranges/commas, any order). None when unparseable."""
    out = set()
    try:
        for part in str(text).replace(" ", "").split(","):
            if not part:
                continue
            if "-" in part:
                a, b = (int(x) for x in part.split("-", 1))
                if a > b:
                    return None
                out |= set(range(a, b + 1))
            else:
                out.add(int(part))
    except ValueError:
        return None
    return out


# ------------------------------------------------------------------ raw profile validation
def validate_raw_profile(profile):
    """Every reason the RAW `mode: pvlan` profile is invalid (empty list = valid).

    Runs before validate_list_of_dicts, so a boolean is never accepted as a VLAN, a null is
    never read as 'unset', and duplicates are refused before any set normalization."""
    errors = []
    if not isinstance(profile, dict):
        return ["profile must be a dictionary"]
    unknown = sorted(k for k in profile if k not in PROFILE_KEYS and k not in INJECTED_KEYS)
    if unknown:
        errors.append("unsupported field(s) for mode 'pvlan': %s" % ", ".join(unknown))
    for key in sorted(k for k in profile if k in PROFILE_KEYS):
        if profile[key] is None:
            errors.append("%s must not be null" % key)
    mode = profile.get("pvlan_mode")
    if mode is None:
        if "pvlan_mode" not in profile:
            errors.append("pvlan_mode is required for mode 'pvlan'")
        return errors
    if mode not in PVLAN_MODES:
        errors.append("pvlan_mode must be one of: %s" % ", ".join(PVLAN_MODES))
        return errors

    pairs = []
    if "pvlan_association" in profile and profile["pvlan_association"] is not None:
        if mode not in ASSOCIATION_MODES:
            errors.append("pvlan_association is not valid for pvlan_mode '%s'" % mode)
        try:
            pairs = requested_pairs("pvlan_association", profile["pvlan_association"])
        except PvlanError as exc:
            errors.append(str(exc))
    if "pvlan_mapping" in profile and profile["pvlan_mapping"] is not None:
        if mode not in MAPPING_MODES:
            errors.append("pvlan_mapping is not valid for pvlan_mode '%s'" % mode)
        try:
            pairs = requested_pairs("pvlan_mapping", profile["pvlan_mapping"])
        except PvlanError as exc:
            errors.append(str(exc))
    errors += limit_errors(mode, pairs)

    for key in ("native_vlan", "allowed_vlans"):
        if key in profile and profile[key] is not None and mode not in TRUNK_MODES:
            errors.append("%s is valid only for pvlan_mode trunk promiscuous or trunk secondary" % key)
    native = profile.get("native_vlan")
    if native is not None:
        if not isinstance(native, str):
            errors.append("native_vlan must be a string")
        elif native != "":
            if not re.match(r"^[1-9][0-9]{0,3}$", native) or not 1 <= int(native) <= 4094:
                errors.append("native_vlan must be '' or one VLAN ID 1-4094")
    allowed = profile.get("allowed_vlans")
    if allowed is not None:
        if not isinstance(allowed, str):
            errors.append("allowed_vlans must be a string")
        elif allowed.strip().lower() == "all":
            errors.append("allowed_vlans 'all' is refused by int_pvlan_host; give explicit ranges")
        elif allowed not in ("", "none"):
            try:
                vlan_set(allowed, "allowed_vlans")
            except PvlanError as exc:
                errors.append(str(exc))

    errors += _companion_errors(profile)
    errors += registry_companion_errors(PVLAN_POLICY, profile)
    return errors


# ------------------------------------------------------------------ companion controls shared by the three parents
# NATIVE_EXTEND rows of the port-channel and vPC parents: public key, nvPair, kind. The public keys are the ones the
# regular port-channel/vPC specs of this module already use for the same nvPair; the helper keeps owning them (no registry).
_NATIVE_POLICY_NAME = re.compile(r"^\S+$")


def native_companion_errors(profile, table):
    """Raw validation of the NATIVE_EXTEND companions of one parent (`table` = PO_/VPC_NATIVE_COMPANIONS). No coercion: a string is
    never read as a boolean or an integer. The values are the template's own (validValues / annotation enum / Min-Max)."""
    errors = []
    for key, _nvp, kind in table:
        if key not in profile or profile[key] is None:
            continue
        value = profile[key]
        if kind == "bool" and not isinstance(value, bool):
            errors.append("%s must be a boolean" % key)
        elif kind == "bpdu" and canonical_native(kind, value) is None:
            errors.append("bpdu_guard must be true, false or 'no' (a boolean, or one of these strings in any letter case)")
        elif kind == "mtu" and value not in ("jumbo", "default"):
            errors.append("mtu must be 'jumbo' or 'default'")
        elif kind == "duplex" and value not in ("auto", "full", "half"):
            errors.append("duplex must be 'auto', 'full' or 'half'")
        elif kind == "speed" and canonical_native(kind, value) is None:
            # RC1: the template's own enum (validValues); whether the switch supports the value is decided by the controller
            # (interface_utility.isPortSpeedSupported) when it builds the intent.
            errors.append("speed must be one of: %s" % ", ".join(SPEED_VALUES))
        elif kind == "lacp_rate" and value not in ("normal", "fast"):
            errors.append("lacp_rate must be 'normal' or 'fast'")
        elif kind == "lacp_prio" and (isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 65535):
            errors.append("lacp_port_priority must be an integer 1-65535")
        elif kind == "policy":
            # The template renders `service-policy type queuing output <name>[ no-stats]`: one name, '' removes it.
            if not isinstance(value, str):
                errors.append("%s must be a string" % key)
            elif value != "" and not _NATIVE_POLICY_NAME.match(value):
                errors.append("%s must be one policy-map name without whitespace, or '' to remove it" % key)
    return errors


def native_companion_wire(kind, value):
    """Wire form of a NATIVE_EXTEND value, the same form the module already sends for the template defaults: booleans as the
    strings "true"/"false", LACP_PORT_PRIO (declared integer) as an integer, bpdu_guard and speed in their canonical spelling
    (canonical_native), everything else unchanged."""
    if kind == "bool":
        return "true" if value else "false"
    if kind == "lacp_prio":
        return int(value)
    if kind in ("bpdu", "speed"):
        return canonical_native(kind, value)
    return value


_NATIVE_SPEC_TYPE = {"bool": "bool", "lacp_prio": "int"}


def native_companion_spec(table):
    """validate_list_of_dicts entries for the native companions of one parent: the declared type and NO default, so an omitted key
    stays omitted (merged keeps HAVE) exactly like the other PVLAN profile keys. The raw profile was validated strictly before."""
    return dict((key, dict(type=_NATIVE_SPEC_TYPE.get(kind, "str"))) for key, _nvp, kind in table)


def apply_native_companions(nv, raw, table):
    """Write every EXPLICIT native companion of `raw` into `nv` (omitted keys leave `nv` untouched)."""
    for key, nvp, kind in table:
        if raw.get(key) is not None:
            nv[nvp] = native_companion_wire(kind, raw[key])
    return nv


def registry_companion_errors(policy, profile):
    """Raw validation of the registry companions of `policy` with the packaged binding's own input contract (type, enum, lengths);
    the message names the field, never the value."""
    errors = []
    for key in sorted(registered_profile_keys(policy)):
        if key not in profile or profile[key] is None:
            continue
        try:
            gie_validate_binding_value(policy, key, profile[key])
        except GieBindingError as exc:
            errors.append(str(exc))
    return errors


def registry_companions(state, policy, raw, have_nv, ndfc_version=None, patch_version=None):
    """WANT of the registry-owned companions of ONE PVLAN parent: (values, blocked).

    `values` maps nvPair -> wire value to place in the outgoing full set; an nvPair not in it keeps whatever the caller states
    for it (the template declaration on a creation, as before C1).
      * explicit key -> gie_contribute_nvpairs: the binding's validation, then the patch_version gate (exact SMU or numeric
        ND >= 4.4.1), then the NDFC floor. A refusal is returned in `blocked`; the module refuses the whole batch with the same
        engine message from the payload builder, before any write.
      * omitted key whose nvPair is in `have_nv` (same parent only; the caller passes None otherwise):
          merged -> the HAVE value;
          replaced/overridden -> gie_withdrawal_action: RESET -> the binding's reset_wire (inferred from the sibling parents,
          NOT measured on a PVLAN parent); NONE or INAPPLICABLE (no approved capability) -> the HAVE value is kept; a value
          that cannot be classified or reset -> blocked. A HAVE value the binding cannot read fails closed (blocked).
    """
    values, blocked = {}, []
    keys = registered_profile_keys(policy)
    explicit = dict((k, raw[k]) for k in keys if k in raw and raw[k] is not None)
    if explicit:
        try:
            add, err = gie_contribute_nvpairs(policy, explicit, ndfc_version, patch_version)
        except GieBindingError as exc:
            add, err = None, str(exc)
        if err:
            return values, [err]
        values.update(add)
    if not isinstance(have_nv, dict):
        return values, blocked
    for key in sorted(keys - set(explicit)):
        nvp = resolve_binding(policy, key)["parent_nvpair"]
        if nvp not in have_nv:
            continue
        have = have_nv[nvp]
        if state == "merged":
            values[nvp] = have
            continue
        try:
            gie_validate_binding_value(policy, key, have, value_source="have")
        except GieBindingError as exc:
            blocked.append(str(exc))
            continue
        if have == "":
            values[nvp] = have  # NDFC's encoding of "no value": nothing to withdraw
            continue
        action, wire = gie_withdrawal_action(policy, key, have, ndfc_version, patch_version)
        if action == GIE_WITHDRAW_RESET:
            values[nvp] = wire
        elif action in (GIE_WITHDRAW_NONE, GIE_WITHDRAW_INAPPLICABLE):
            values[nvp] = have
        else:
            blocked.append("omitted field '%s' differs from its template default on this %s and no verified reset exists; "
                           "state it explicitly" % (key, policy))
    return values, blocked


def _companion_errors(profile):
    errors = []
    for key, _nv, kind, _default in COMPANIONS:
        if key not in profile or profile[key] is None:
            continue
        value = profile[key]
        if kind == "bool" and not isinstance(value, bool):
            errors.append("%s must be a boolean" % key)
        elif kind == "str":
            if not isinstance(value, str):
                errors.append("%s must be a string" % key)
            elif key == "description" and len(value) > 254:
                errors.append("description exceeds 254 characters")
        elif kind == "bpdu" and canonical_native(kind, value) is None:
            errors.append("bpdu_guard must be true, false or 'no' (a boolean, or one of these strings in any letter case)")
        elif kind == "mtu" and value not in ("jumbo", "default"):
            errors.append("mtu must be 'jumbo' or 'default'")
        elif kind == "speed" and canonical_native(kind, value) is None:
            errors.append("speed must be one of: %s" % ", ".join(SPEED_VALUES))
        elif kind == "duplex" and value not in ("auto", "full", "half"):
            errors.append("duplex must be 'auto', 'full' or 'half'")
        elif kind == "conf":
            lines = cmds_lines(value)
            if lines is None and isinstance(value, str):
                errors.append("cmds given as text must not contain a comma; use a list of strings")
            elif lines is None:
                errors.append("cmds must be a list of strings (or a text with one command per line)")
            elif any(_CONF_FORBIDDEN.search(x) for x in lines):
                errors.append("cmds must not manage private-vlan or switchport settings; use the structured pvlan fields")
    if profile.get("qos_policy") and profile.get("enable_qos") is False:
        errors.append("qos_policy requires enable_qos true")
    return errors


def requested_pairs(field, rows):
    """Validated public rows -> sorted [(P, S)]; duplicate logical pairs are refused."""
    if not isinstance(rows, list):
        raise PvlanError("%s must be a list" % field)
    pairs = []
    for index, row in enumerate(rows):
        where = "%s[%d]" % (field, index)
        if not isinstance(row, dict):
            raise PvlanError("%s must be a dictionary" % where)
        want_keys = {"primary_vlan", "secondary_vlan"} if field == "pvlan_association" else {"primary_vlan", "secondary_vlans"}
        if set(row) != want_keys:
            raise PvlanError("%s must have exactly the keys: %s" % (where, ", ".join(sorted(want_keys))))
        primary = vlan_id(row["primary_vlan"], where + ".primary_vlan")
        if field == "pvlan_association":
            secondaries = [vlan_id(row["secondary_vlan"], where + ".secondary_vlan")]
        else:
            secondaries = vlan_set(row["secondary_vlans"], where + ".secondary_vlans")
        for s in secondaries:
            if s == primary:
                raise PvlanError("%s associates VLAN %d with itself" % (where, s))
            pairs.append((primary, s))
    if len(set(pairs)) != len(pairs):
        raise PvlanError("%s repeats a (primary, secondary) pair" % field)
    return sorted(pairs)


def limit_errors(mode, pairs):
    """Template limits (T add()): host <= 1 row; promiscuous one primary; trunk secondary one
    secondary per primary. Applied to raw input AND again after a merged union.
    N06: in every mode a secondary VLAN belongs to ONE primary within the interface's (or vPC's)
    resulting list; the same pair twice is one pair (set), other interfaces are never consulted."""
    pairs = sorted(set(pairs))
    if mode == MODE_HOST and len(pairs) > 1:
        return ["pvlan_mode host allows at most one association"]
    if mode == MODE_PROMISCUOUS and len({p for p, _s in pairs}) > 1:
        return ["pvlan_mode promiscuous allows a single primary VLAN in its mapping"]
    if mode == MODE_TRUNK_SECONDARY:
        primaries = [p for p, _s in pairs]
        if len(primaries) != len(set(primaries)):
            return ["pvlan_mode trunk secondary allows one secondary VLAN per primary VLAN"]
    owners = {}
    for p, s in pairs:
        owners.setdefault(s, []).append(p)
    return [
        "pvlan_mode %s: secondary VLAN %d is associated with more than one primary VLAN (%s); a secondary VLAN belongs to "
        "one primary VLAN" % (mode, s, ", ".join(str(p) for p in owners[s]))
        for s in sorted(owners) if len(owners[s]) > 1
    ]


# ------------------------------------------------------------------ list wire form
def pairs_from_wire(raw, key):
    """Authoritative HAVE list -> sorted [(P, S)]. '' and the empty wrapper are empty; integer
    or string IDs and range S_VLAN are parsed semantically. Null, malformed, ambiguous or
    duplicated content raises PvlanError (never read as empty)."""
    if raw == "":
        return []
    if not isinstance(raw, str):
        raise PvlanError("%s is %s, not a wrapper string" % (key, type(raw).__name__))
    try:
        data = json.loads(raw)
    except ValueError:
        try:
            data = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            raise PvlanError("%s is not a parseable wrapper" % key)
    if not isinstance(data, dict) or set(data) != {key} or not isinstance(data[key], list):
        raise PvlanError("%s wrapper is malformed" % key)
    pairs = []
    for row in data[key]:
        if not isinstance(row, dict) or "P_VLAN" not in row:
            raise PvlanError("%s row is malformed" % key)
        p = _wire_int(row["P_VLAN"], key)
        s_raw = row.get("S_VLAN")
        if _is_int(s_raw) or (isinstance(s_raw, str) and s_raw.isdigit()):
            secondaries = [_wire_int(s_raw, key)]
        elif isinstance(s_raw, str):
            parsed = _lenient_vlan_set(s_raw)
            if not parsed or any(not 1 <= v <= 4094 for v in parsed):
                raise PvlanError("%s secondary %r is malformed" % (key, s_raw))
            secondaries = sorted(parsed)
        else:
            raise PvlanError("%s secondary is missing or malformed" % key)
        pairs += [(p, s) for s in secondaries]
    if len(set(pairs)) != len(pairs):
        raise PvlanError("%s holds duplicate pairs" % key)
    return sorted(pairs)


def _wire_int(value, key):
    if _is_int(value):
        v = value
    elif isinstance(value, str) and value.isdigit():
        v = int(value)
    else:
        raise PvlanError("%s VLAN %r is malformed" % (key, value))
    if not 1 <= v <= 4094:
        raise PvlanError("%s VLAN %d is outside 1-4094" % (key, v))
    return v


def pairs_to_wire(key, pairs):
    """Canonical wire: one row per pair, string IDs, sorted. [] -> the empty wrapper."""
    rows = [{"P_VLAN": str(p), "S_VLAN": str(s)} for p, s in sorted(set(pairs))]
    return json.dumps({key: rows}, separators=(",", ":"))


def allowed_equal(a, b):
    """'' (unset) and 'none' stay distinct; numeric sets compare semantically."""
    a = "" if a is None else str(a).strip()
    b = "" if b is None else str(b).strip()
    if a == b:
        return True
    if a.lower() == "none" or b.lower() == "none" or a == "" or b == "":
        return a.lower() == b.lower()
    sa, sb = _lenient_vlan_set(a), _lenient_vlan_set(b)
    return sa is not None and sa == sb


def native_equal(a, b):
    a = "" if a is None else str(a).strip()
    b = "" if b is None else str(b).strip()
    return a == b


def _bool_wire(value):
    return "true" if str(value).strip().lower() == "true" else "false"


def companion_wire(key, value):
    kind = COMPANION_BY_KEY[key][2]
    if kind == "bool":
        return _bool_wire(value)
    if kind == "conf":
        return "\n".join(cmds_lines(value))
    if kind in ("bpdu", "speed"):
        return canonical_native(kind, value)
    return value


def _companion_equal(kind, a, b):
    if kind == "bool":
        return str(a).strip().lower() == str(b).strip().lower()
    if kind in ("mtu", "speed", "duplex", "bpdu"):
        return str(a).strip().lower() == str(b).strip().lower()
    if kind == "conf":
        return [l.rstrip() for l in str(a).splitlines() if l.strip()] == [l.rstrip() for l in str(b).splitlines() if l.strip()]
    return a == b


def active_list_key(mode):
    return ASSOCIATION_LIST if mode in ASSOCIATION_MODES else MAPPING_LIST


def promiscuous_partial_removal(have_mode, want_mode, have_pairs, want_pairs):
    """The demonstrated non-trunk defect: retained promiscuous mapping that would
    lose an existing pair while a mapping remains. Mixed remove+add is included on purpose."""
    return have_mode == MODE_PROMISCUOUS and want_mode == MODE_PROMISCUOUS and bool(have_pairs) and bool(want_pairs) and bool(set(have_pairs) - set(want_pairs))


# ------------------------------------------------------------------ reconciliation
def reconcile(state, raw_profile, ifname, have_policy, have_nv, ndfc_version=None, patch_version=None):
    """WANT vs authoritative HAVE for one int_pvlan_host target.

    raw_profile: the user's raw profile (presence = key in dict; already validated).
    have_policy/have_nv: current policy and nvPairs, or (None, None) when the target has no
    readable direct policy (the caller refuses that before calling).
    ndfc_version/patch_version: the caller's controller context, used ONLY by the registry
    companions (disable_lldp_transmit/receive); the PVLAN core never depends on them.

    Returns dict(nv=<full outgoing nvPairs>, changed=<reported nvPairs>, update=<bool>,
    blocked=[reasons], new_secondaries=[(P, S)] needing a type check, mode=<want mode>).
    """
    out = {"nv": {}, "changed": {}, "update": False, "blocked": [], "new_secondaries": [], "mode": None}
    present = set(k for k in raw_profile if k in PROFILE_KEYS)
    mode = raw_profile["pvlan_mode"]
    out["mode"] = mode
    same_policy = have_policy == PVLAN_POLICY
    have_nv = have_nv or {}
    merged = state == "merged"

    have_mode = None
    have_pairs = {ASSOCIATION_LIST: [], MAPPING_LIST: []}
    if same_policy:
        have_mode = have_nv.get("PVLAN_MODE")
        if have_mode not in PVLAN_MODES:
            raise PvlanError("current PVLAN_MODE %r is not a known int_pvlan_host mode" % (have_mode,))
        for key in (ASSOCIATION_LIST, MAPPING_LIST):
            have_pairs[key] = pairs_from_wire(have_nv.get(key, ""), key)
        lost = sorted(k for k in have_nv if k not in KNOWN_HAVE_NVPAIRS and have_nv[k] not in ("", None))
        if lost:
            out["blocked"].append("current policy holds nvPair(s) this module cannot classify and a full-set " "update could clear: %s" % ", ".join(lost))
        if merged and mode != have_mode:
            out["blocked"].append("pvlan_mode change %r -> %r requires state replaced or overridden; merged " "never converts the submode" % (have_mode, mode))
    mode_change = same_policy and mode != have_mode

    nv = out["nv"]
    nv["PVLAN_MODE"] = mode
    nv["INTF_NAME"] = ifname

    # ---- native lists
    active = active_list_key(mode)
    field = "pvlan_association" if active == ASSOCIATION_LIST else "pvlan_mapping"
    requested = requested_pairs(field, raw_profile[field]) if field in present else None
    current = have_pairs[active] if (same_policy and not mode_change) else []
    if merged and same_policy and not mode_change:
        desired = sorted(set(current) | set(requested or []))
    else:
        desired = sorted(set(requested or []))
    out["blocked"] += limit_errors(mode, desired)
    if promiscuous_partial_removal(have_mode if not mode_change else None, mode, current, desired):
        out["blocked"].append(
            "removing secondary VLAN(s) %s from a promiscuous mapping that keeps other "
            "secondaries is blocked: the controller generates an invalid removal command for "
            "this transition (measured). Clear the mapping explicitly, or use trunk promiscuous"
            % ", ".join("%d/%d" % p for p in sorted(set(current) - set(desired)))
        )
    for key in (ASSOCIATION_LIST, MAPPING_LIST):
        have_raw = have_nv.get(key, "") if same_policy else None
        target = desired if key == active else []
        have_list = have_pairs[key] if same_policy else None
        if have_list is not None and sorted(target) == have_list:
            nv[key] = have_raw if key in have_nv else ""
        elif not target and (have_list is None or not have_list):
            nv[key] = ""
        else:
            nv[key] = pairs_to_wire(key, target)
    if mode == MODE_TRUNK_SECONDARY:
        prior = set(have_pairs[ASSOCIATION_LIST]) if (same_policy and have_mode == MODE_TRUNK_SECONDARY) else set()
        out["new_secondaries"] = sorted(set(desired) - prior)

    # ---- trunk scalars
    for key, nvp, eq in (("native_vlan", NATIVE_VLAN, native_equal), ("allowed_vlans", ALLOWED_VLANS, allowed_equal)):
        have_raw = have_nv.get(nvp, "") if same_policy else ""
        if mode not in TRUNK_MODES:
            value = ""
        elif key in present:
            value = raw_profile[key]
        elif merged and same_policy and not mode_change:
            value = have_raw
        else:
            value = ""
        nv[nvp] = have_raw if (same_policy and eq(value, have_raw)) else value

    # ---- companions
    for key, nvp, kind, default in COMPANIONS:
        have_raw = have_nv.get(nvp) if same_policy else None
        if key in present:
            value = companion_wire(key, raw_profile[key])
            if kind == "conf" and merged and same_policy and have_raw:
                have_lines = str(have_raw).split("\n")
                extra = [l for l in cmds_lines(raw_profile[key]) if l not in have_lines]
                value = "\n".join(have_lines + extra) if extra else have_raw
        elif merged and same_policy and have_raw is not None:
            value = have_raw
        else:
            value = default
        if same_policy and have_raw is not None and _companion_equal(kind, value, have_raw):
            value = have_raw
        nv[nvp] = value
    # A requested policy name needs QoS enabled in the RESULTING state ("qos_policy is only valid when enable_qos is true";
    # the template renders the policy only with ENABLE_QOS true). An omitted enable_qos resolves from HAVE under merged and
    # to the template default false otherwise. A name kept from HAVE while QoS is disabled is not refused.
    if raw_profile.get("qos_policy") and str(nv.get("ENABLE_QOS", "false")).strip().lower() != "true":
        out["blocked"].append("qos_policy requires enable_qos true (the template ignores the policy while QoS is disabled); set "
                              "enable_qos true in the same request or remove qos_policy")

    # ---- registry companions. On the SAME policy the registry owns lldpTransmit/lldpReceive: an explicit value always
    # wins over the old preservation, and an omitted one follows the engine (merged keeps HAVE; replaced withdraws or, without an
    # approved capability, keeps HAVE). HAVE's own spelling is kept when the value is the same.
    reg_values, reg_blocked = registry_companions(state, PVLAN_POLICY, raw_profile, have_nv if same_policy else None,
                                                  ndfc_version, patch_version)
    out["blocked"] += reg_blocked
    for nvp, value in reg_values.items():
        have_raw = have_nv.get(nvp) if same_policy else None
        nv[nvp] = have_raw if (have_raw is not None and _companion_equal("bool", value, have_raw)) else value

    # ---- preservation-only, never owned here (a value the registry resolved above is not overwritten; a policy change still
    # carries the HAVE lldp booleans exactly as before C1)
    if have_nv:
        for nvp in PRESERVE_ALWAYS + (PRESERVE_SAME_POLICY if same_policy else ()):
            if nvp in reg_values:
                continue
            if nvp in have_nv and str(have_nv[nvp]).strip().lower() in ("true", "false"):
                nv[nvp] = have_nv[nvp]

    # ---- reported diff and update decision: the same values that are sent. A key HAVE does
    # not return compares against the template default, so absence is not a perpetual change.
    if not same_policy:
        out["changed"] = dict(nv)
        out["update"] = True
    else:
        for k, v in nv.items():
            if k in have_nv:
                if have_nv[k] != v:
                    out["changed"][k] = v
            elif v != _ABSENT_DEFAULT.get(k, object()):
                out["changed"][k] = v
        out["update"] = bool(out["changed"])
    return out


_ABSENT_DEFAULT = dict([(c[1], c[3]) for c in COMPANIONS] + [(ASSOCIATION_LIST, ""), (MAPPING_LIST, ""), (NATIVE_VLAN, ""), (ALLOWED_VLANS, ""),
                                                             # The template declares both false (int_pvlan_host L61-L70)
                                                             ("lldpTransmit", "false"), ("lldpReceive", "false")])


# ------------------------------------------------------------------ CLI transition model
class Model(object):
    """scalars/pairs: the OWNED lines of an interface (rendered, or observed inside the
    transition's vocabulary). foreign: observed lines outside that vocabulary; they are never
    removable and never create an obligation to remove them."""

    def __init__(self, scalars, list_kind, pairs, modeled, foreign=()):
        self.scalars = set(scalars)
        self.list_kind = list_kind
        self.pairs = set(pairs)
        self.modeled = modeled
        self.foreign = set(foreign)


_LIST_LINE = {
    MODE_HOST: re.compile(r"^switchport private-vlan host-association ([0-9]+) ([0-9,\-]+)$"),
    MODE_PROMISCUOUS: re.compile(r"^switchport private-vlan mapping ([0-9]+) ([0-9,\-]+)$"),
    MODE_TRUNK_PROMISCUOUS: re.compile(r"^switchport private-vlan mapping trunk ([0-9]+) ([0-9,\-]+)$"),
    MODE_TRUNK_SECONDARY: re.compile(r"^switchport private-vlan association trunk ([0-9]+) ([0-9,\-]+)$"),
}
_TRUNK_REMOVE = re.compile(r"^switchport private-vlan mapping trunk ([0-9]+) remove ([0-9,\-]+)$")

# ------------------------------------------------------------------ owned CLI vocabulary
# The interface commands each modeled policy's installed add() can render (int_pvlan_host
# 5c227412..., int_trunk_host 99dc8f0a...), as line grammars, and the command namespaces of the
# fields those policies own. The PVLAN operation owns (may change or withdraw) a device line only
# when it matches the grammar of a policy on either side of the requested transition, or is a
# freeform CONF line of either side. Presence on the device authorizes nothing by itself.
_COMPANION_GRAMMAR = (
    r"mtu [0-9]+",
    r"spanning-tree bpduguard (enable|disable)",
    r"spanning-tree port type edge trunk",
    r"description .+",
    r"no cdp enable",
    r"no lldp (transmit|receive)",
    r"vpc orphan-port suspend",
    r"duplex \S+",
    r"(no )?shutdown",
    r"priority-flow-control mode on",
    r"priority-flow-control watch-dog-interval on",
    r"service-policy type qos input \S+",
    r"service-policy type queuing output \S+",
)
_GRAMMAR = {
    PVLAN_POLICY: _COMPANION_GRAMMAR
    + (
        # RC1: int_pvlan_host renders `speed <n>` and, by device capability, `no negotiate auto` (HOST 354-361 [SRC]).
        r"speed [0-9]+",
        r"no negotiate auto",
        r"switchport",
        r"switchport mode private-vlan (host|promiscuous|trunk promiscuous|trunk secondary)",
        r"switchport private-vlan trunk native vlan [0-9]+",
        r"switchport private-vlan trunk allowed vlan [0-9,\-]+",
        r"switchport private-vlan host-association [0-9]+ [0-9,\-]+",
        r"switchport private-vlan mapping [0-9]+ [0-9,\-]+",
        r"switchport private-vlan mapping trunk [0-9]+ [0-9,\-]+",
        r"switchport private-vlan association trunk [0-9]+ [0-9,\-]+",
    ),
    TRUNK_HOST_POLICY: _COMPANION_GRAMMAR
    + (
        r"switchport",
        r"switchport mode trunk",
        r"switchport trunk allowed vlan \S+",
        r"switchport trunk native vlan [0-9]+",
        r"flowcontrol (receive|send) on",
        r"spanning-tree bpdufilter \S+",
        r"spanning-tree link-type \S+",
        r"spanning-tree guard \S+",
        r"spanning-tree port type \S+( trunk)?",
        r"bandwidth (inherit )?\S+",
        r"link debounce (link-up )?time \S+",
        r"no errdisable port detect cause acl-exception",
        r"fec \S+",
        r"storm-control action \S+",
        r"service-policy type (qos input|queuing output) \S+ no-stats",
        r"ip port access-group \S+ in",
    ),
}
_COMPANION_NAMESPACES = (
    "switchport",
    "mtu",
    "spanning-tree",
    "description",
    "cdp",
    "lldp",
    "vpc orphan-port",
    "duplex",
    "speed",
    "shutdown",
    "priority-flow-control",
    "service-policy",
)
_NAMESPACES = {
    PVLAN_POLICY: _COMPANION_NAMESPACES,
    TRUNK_HOST_POLICY: _COMPANION_NAMESPACES
    + (
        "flowcontrol",
        "bandwidth",
        "link debounce",
        "errdisable",
        "fec",
        "storm-control",
        "ip port access-group",
    ),
}
VOCABULARY_POLICIES = tuple(sorted(_GRAMMAR))


# Grammars of the regular port-channel host policy and of its PVLAN member
# policy. Kept in their OWN tables so the Ethernet tables, VOCABULARY_POLICIES and
# DEFAULT_VOCABULARY above stay byte-for-byte as defined: no Ethernet decision can change.
PO_HOST_POLICY = "int_port_channel_pvlan_host"
PO_MEMBER_POLICY = "int_port_channel_pvlan_member"

_PO_LIST_GRAMMAR = (
    r"switchport private-vlan trunk native vlan [0-9]+",
    r"switchport private-vlan trunk allowed vlan [0-9,\-]+",
    r"switchport private-vlan host-association [0-9]+ [0-9,\-]+",
    r"switchport private-vlan mapping [0-9]+ [0-9,\-]+",
    r"switchport private-vlan mapping trunk [0-9]+ [0-9,\-]+",
    r"switchport private-vlan association trunk [0-9]+ [0-9,\-]+",
)
_PO_GRAMMAR = {
    PO_HOST_POLICY: _COMPANION_GRAMMAR
    + (
        r"switchport",
        r"switchport mode private-vlan (host|promiscuous|trunk promiscuous|trunk secondary)",
        r"spanning-tree port type \S+( trunk)?",
        r"no lacp suspend-individual",
        r"speed \S+",
        r"no negotiate auto",
        # HOST:495-498 appends ` no-stats` to the queuing line when queuingStats is true (Po table only: the
        # Ethernet tables are unchanged).
        r"service-policy type queuing output \S+ no-stats",
    )
    + _PO_LIST_GRAMMAR,
    # The member's own template lines + the parent's 'Inherited Commands' int_eth child on the member (HOST:507-560).
    PO_MEMBER_POLICY: (
        r"switchport",
        r"switchport mode private-vlan (host|promiscuous|trunk promiscuous|trunk secondary)",
        # Measured: the pending carries the COMMAND
        # `channel-group N force mode M` and the controller's expected holds `channel-group N mode M`. That the device keeps
        # the same no-force form is the NX-OS convention, NOT observed on the switch: live acceptance must check it.
        r"channel-group [0-9]+ force( mode (active|passive))?",
        r"channel-group [0-9]+( mode (active|passive))?",
        r"description .+",
        r"no cdp enable",
        r"no lldp (transmit|receive)",
        r"lacp port-priority [0-9]+",
        r"lacp rate \S+",
        r"(no )?shutdown",
        r"mtu [0-9]+",
        r"speed \S+",
        r"no negotiate auto",
        r"duplex \S+",
    )
    + _PO_LIST_GRAMMAR,
}
_PO_NAMESPACES = {
    PO_HOST_POLICY: _COMPANION_NAMESPACES + ("lacp", "negotiate"),
    PO_MEMBER_POLICY: ("switchport", "channel-group", "description", "cdp", "lldp", "lacp", "shutdown", "mtu", "speed",
                       "negotiate", "duplex"),
}
PO_VOCABULARY_POLICIES = tuple(sorted(_PO_GRAMMAR))
# The vPC child policy keeps its OWN tables, filled in the vPC section below, so PO_VOCABULARY_POLICIES and
# every Po/Ethernet decision stay what they were.
_VPC_GRAMMAR = {}
_VPC_NAMESPACES = {}

# Measured (one Ethernet member, NX-OS 10.5(5), NDFC 12.6.0.267): the ONLY device lines a member
# PREPARED as access or routed may hold when it joins a trunk secondary port-channel. Access (int_access_host): `shutdown`,
# `spanning-tree port type edge`, `mtu 9216`; routed (int_routed_host): `no switchport`, `mtu 9216` (shutdown is the L3 default
# and is NOT shown). Their field namespaces include switchport/ip/ipv6/vrf so any other line there is uninterpretable (refused).
# Own table: VOCABULARY_POLICIES, PO_VOCABULARY_POLICIES and DEFAULT_VOCABULARY stay byte-for-byte as defined.
PO_ACCESS_BASELINE_POLICY = "int_access_host"
PO_ROUTED_BASELINE_POLICY = "int_routed_host"
_PO_BASELINE_GRAMMAR = {
    PO_ACCESS_BASELINE_POLICY: (r"(no )?shutdown", r"spanning-tree port type edge", r"mtu [0-9]+"),
    PO_ROUTED_BASELINE_POLICY: (r"(no )?shutdown", r"no switchport", r"mtu [0-9]+"),
}
_PO_BASELINE_NAMESPACES = {
    PO_ACCESS_BASELINE_POLICY: ("switchport", "spanning-tree", "mtu", "shutdown", "ip", "ipv6", "vrf"),
    PO_ROUTED_BASELINE_POLICY: ("switchport", "spanning-tree", "mtu", "shutdown", "ip", "ipv6", "vrf"),
}


class Vocabulary(object):
    """What one requested transition owns. owns(line): the operation may change/withdraw it.
    interferes(line): a line it does NOT own falls in a field namespace it does own, so the
    model cannot interpret the device state there."""

    def __init__(self, policies, freeform=()):
        self.policies = tuple(sorted(set(
            p for p in policies if p in _GRAMMAR or p in _PO_GRAMMAR or p in _PO_BASELINE_GRAMMAR or p in _VPC_GRAMMAR)))
        grammar = [g for p in self.policies for g in (_GRAMMAR.get(p) or _PO_GRAMMAR.get(p) or _PO_BASELINE_GRAMMAR.get(p) or _VPC_GRAMMAR[p])]
        self._grammar = re.compile("^(?:%s)$" % "|".join(grammar)) if grammar else None
        self.freeform = frozenset(freeform)
        self._prefixes = tuple(sorted(set(
            n for p in self.policies for n in (
                _NAMESPACES.get(p) or _PO_NAMESPACES.get(p) or _PO_BASELINE_NAMESPACES.get(p) or _VPC_NAMESPACES[p]))))

    def owns(self, line):
        return line in self.freeform or bool(self._grammar and self._grammar.match(line))

    def interferes(self, line):
        bare = line[3:] if line.startswith("no ") else line
        return any(bare == p or bare.startswith(p + " ") for p in self._prefixes)


def _conf_lines(policy, nv):
    # RC1: the port-channel host and the vPC child own their freeform CONF exactly like the Ethernet PVLAN policy.
    if (policy not in _GRAMMAR and policy not in (PO_HOST_POLICY, VPC_PO_POLICY)) or not isinstance(nv, dict):
        return []
    return [line.strip() for line in str(nv.get("CONF", "") or "").split("\n") if line.strip()]


def transition_vocabulary(pre, post):
    """Vocabulary of one requested transition, from the (policy, nvPairs) on each side: the
    grammars of both policies plus the freeform CONF lines of both sides. A policy outside the
    modeled vocabulary contributes nothing, so its device lines stay foreign."""
    pre, post = pre or (None, None), post or (None, None)
    return Vocabulary((pre[0], post[0]), _conf_lines(*pre) + _conf_lines(*post))


DEFAULT_VOCABULARY = Vocabulary(VOCABULARY_POLICIES)


def render(policy, nv):
    """Positive interface-body lines for a policy instance.

    int_pvlan_host follows the installed template's add() (sha256 5c227412...). int_trunk_host
    follows the installed template's add() (sha256 99dc8f0a788d...). Values whose rendering depends on device capability or
    fabric settings (a speed outside SPEED_CLI, AI/ML QoS fallback, PFC watchdog, storm-control levels,
    NetFlow, VLAN mapping) make the Model unmodeled; any other policy is unmodeled too. An
    unmodeled DESTINATION is refused before any write; an unmodeled line in a fresh pending is
    refused before deploy."""
    nv = nv or {}
    s = set()
    if policy == PVLAN_POLICY:
        mode = nv.get("PVLAN_MODE")
        if mode not in PVLAN_MODES or not _pvlan_values_modeled(nv):
            return Model((), None, (), False)
        s.add("switchport")
        s.add("switchport mode private-vlan %s" % mode)
        native = str(nv.get(NATIVE_VLAN, "") or "").strip()
        if native and native != "1":
            s.add("switchport private-vlan trunk native vlan %s" % native)
        allowed = str(nv.get(ALLOWED_VLANS, "") or "").strip()
        if allowed:
            s.add("switchport private-vlan trunk allowed vlan %s" % allowed)
        key = active_list_key(mode)
        pairs = pairs_from_wire(nv.get(key, "") or "", key)
        _render_companions(nv, s)
        return Model(s, mode, pairs, True)
    if policy == TRUNK_HOST_POLICY:
        return _render_trunk_host(nv)
    if policy == PO_HOST_POLICY:
        return _render_po_host(nv)
    if policy == PO_MEMBER_POLICY:
        return _render_po_member(nv)
    if policy == VPC_PO_POLICY:
        return _render_vpc_po(nv)
    if policy == PO_ROUTED_BASELINE_POLICY:
        return _render_routed_released(nv)
    return Model((), None, (), False)


def _flag(nv, key, default):
    value = nv.get(key, default)
    return default if value is None else str(value).strip().lower()


def _text(nv, key):
    value = nv.get(key, "")
    return "" if value is None else str(value).strip()


def speed_cli(nv):
    """RC1: "" for Auto (no line), the `speed` keyword of a known enum value, None for anything else (unmodeled)."""
    value = _text(nv, "SPEED")
    if value in ("", "Auto"):
        return ""
    return SPEED_CLI.get(value)


def adopt_capability_lines(desired, controller):
    """RC1: the intended Model with the controller's `no negotiate auto` adopted, when (and only when) the intended state renders a
    non-Auto speed line and the controller's expected configuration holds that exact line. The line depends on device capability that
    the module cannot read; nothing else is ever adopted, and without a speed line it stays a disagreement."""
    if not (desired.modeled and controller.modeled) or NEGOTIATE_CAPABILITY_LINE in desired.scalars:
        return desired
    if not any(_SPEED_LINE.match(line) for line in desired.scalars) or NEGOTIATE_CAPABILITY_LINE not in controller.scalars:
        return desired
    return Model(desired.scalars | set((NEGOTIATE_CAPABILITY_LINE,)), desired.list_kind, desired.pairs, True, desired.foreign)


def _pvlan_values_modeled(nv):
    if speed_cli(nv) is None:
        return False
    if _flag(nv, "ENABLE_QOS", "false") == "true" and not _text(nv, "QOS_POLICY"):
        return False
    return _flag(nv, "MTU", "jumbo") in ("jumbo", "default")


def _render_trunk_host(nv):
    """int_trunk_host add() for the values this module can send (template 99dc8f0a...)."""
    s = set()
    allowed = _text(nv, "ALLOWED_VLANS")
    mtu = _flag(nv, "MTU", "jumbo")
    if (
        not allowed
        or _text(nv, "SPEED") not in ("", "Auto")
        or mtu not in ("jumbo", "default")
        or _flag(nv, "ENABLE_PFC", "false") == "true"
        or (_flag(nv, "ENABLE_QOS", "false") == "true" and not _text(nv, "QOS_POLICY"))
        or _flag(nv, "ENABLE_NETFLOW", "false") == "true"
        or _flag(nv, "enableVlanMapping", "false") == "true"
        or any(
            _text(nv, k)
            for k in (
                "STORM_CONTROL_BCAST_LEVEL_PERCENT",
                "STORM_CONTROL_MCAST_LEVEL_PERCENT",
                "STORM_CONTROL_UCAST_LEVEL_PERCENT",
                "STORM_CONTROL_BCAST_LEVEL_PPS",
                "STORM_CONTROL_MCAST_LEVEL_PPS",
                "STORM_CONTROL_UCAST_LEVEL_PPS",
            )
        )
    ):
        return Model((), None, (), False)
    s.update(("switchport", "switchport mode trunk", "switchport trunk allowed vlan %s" % allowed))
    if mtu == "jumbo":
        s.add("mtu 9216")
    for key, line in (("flowcontrolReceive", "flowcontrol receive on"), ("flowcontrolSend", "flowcontrol send on")):
        if _flag(nv, key, "off") == "on":
            s.add(line)
    bpdu = _flag(nv, "BPDUGUARD_ENABLED", "no")
    if bpdu == "true":
        s.add("spanning-tree bpduguard enable")
    elif bpdu == "false":
        s.add("spanning-tree bpduguard disable")
    for key, skip, fmt in (
        ("BPDUFILTER_ENABLED", "no", "spanning-tree bpdufilter %s"),
        ("LINK_TYPE", "auto", "spanning-tree link-type %s"),
        ("GUARD_MODE", "no", "spanning-tree guard %s"),
    ):
        value = _text(nv, key)
        if value and value.lower() != skip:
            s.add(fmt % value)
    port_type = _text(nv, "spanningTreePortType")
    if port_type and port_type.lower() != "no":
        s.add("spanning-tree port type %s" % port_type)
    elif _flag(nv, "PORTTYPE_FAST_ENABLED", "true") == "true":
        s.add("spanning-tree port type edge trunk")
    native = _text(nv, "NATIVE_VLAN")
    if native and native != "1":
        s.add("switchport trunk native vlan %s" % native)
    if _text(nv, "DESC"):
        s.add("description %s" % _text(nv, "DESC"))
    if _flag(nv, "CDP_ENABLE", "true") == "false":
        s.add("no cdp enable")
    if _flag(nv, "lldpTransmit", "false") == "true":
        s.add("no lldp transmit")
    if _flag(nv, "lldpReceive", "false") == "true":
        s.add("no lldp receive")
    if _flag(nv, "ENABLE_ORPHAN_PORT", "false") == "true":
        s.add("vpc orphan-port suspend")
    duplex = _flag(nv, "PORT_DUPLEX_MODE", "auto")
    if duplex != "auto":
        s.add("duplex %s" % duplex)
    for key, fmt, skip in (
        ("BANDWIDTH", "bandwidth %s", ""),
        ("INHERIT_BW", "bandwidth inherit %s", ""),
        ("DEBOUNCE_TIMER", "link debounce time %s", "100"),
        ("DEBOUNCE_LINKUP_TIMER", "link debounce link-up time %s", ""),
    ):
        value = _text(nv, key)
        if value and value != skip:
            s.add(fmt % value)
    if _flag(nv, "ENABLE_ERRDISABLE_ACL", "true") == "false":
        s.add("no errdisable port detect cause acl-exception")
    fec = _text(nv, "FEC")
    if fec and fec.lower() != "auto":
        s.add("fec %s" % fec)
    action = _text(nv, "STORM_CONTROL_ACTION")
    if action and action.lower() != "no":
        s.add("storm-control action %s" % action)
    s.add("no shutdown" if _flag(nv, "ADMIN_STATE", "true") == "true" else "shutdown")
    if _flag(nv, "ENABLE_QOS", "false") == "true":
        stats = " no-stats" if _flag(nv, "qosStatsSuppressed", "false") == "true" else ""
        s.add("service-policy type qos input %s%s" % (_text(nv, "QOS_POLICY"), stats))
    if _text(nv, "QUEUING_POLICY"):
        stats = " no-stats" if _flag(nv, "queuingStats", "false") == "true" else ""
        s.add("service-policy type queuing output %s%s" % (_text(nv, "QUEUING_POLICY"), stats))
    if _text(nv, "aclFilter"):
        s.add("ip port access-group %s in" % _text(nv, "aclFilter"))
    for line in str(nv.get("CONF", "") or "").split("\n"):
        if line.strip():
            s.add(line.strip())
    return Model(s, None, (), True)


def _render_companions(nv, s):
    def flag(k, default):
        return str(nv.get(k, default)).strip().lower()

    if str(nv.get("MTU", "jumbo")).strip().lower() == "jumbo":
        s.add("mtu 9216")
    bpdu = flag("BPDUGUARD_ENABLED", "no")
    if bpdu == "true":
        s.add("spanning-tree bpduguard enable")
    elif bpdu == "false":
        s.add("spanning-tree bpduguard disable")
    if flag("PORTTYPE_FAST_ENABLED", "true") == "true":
        s.add("spanning-tree port type edge trunk")
    if nv.get("DESC"):
        s.add("description %s" % nv["DESC"])
    if flag("CDP_ENABLE", "true") == "false":
        s.add("no cdp enable")
    if flag("lldpTransmit", "false") == "true":
        s.add("no lldp transmit")
    if flag("lldpReceive", "false") == "true":
        s.add("no lldp receive")
    if flag("ENABLE_ORPHAN_PORT", "false") == "true":
        s.add("vpc orphan-port suspend")
    duplex = flag("PORT_DUPLEX_MODE", "auto")
    if duplex != "auto":
        s.add("duplex %s" % duplex)
    if speed_cli(nv):
        s.add("speed %s" % speed_cli(nv))
    s.add("no shutdown" if flag("ADMIN_STATE", "true") == "true" else "shutdown")
    for line in str(nv.get("CONF", "") or "").split("\n"):
        if line.strip():
            s.add(line.strip())
    if flag("ENABLE_PFC", "false") == "true":
        s.add("priority-flow-control mode on")
        s.add("priority-flow-control watch-dog-interval on")
    if flag("ENABLE_QOS", "false") == "true" and nv.get("QOS_POLICY"):
        s.add("service-policy type qos input %s" % nv["QOS_POLICY"])
    if nv.get("QUEUING_POLICY"):
        s.add("service-policy type queuing output %s" % nv["QUEUING_POLICY"])


# ------------------------------------------------------------------ fresh pending validation
LEGACY_PREVIEW_STATUS = {"In-Sync": False, "Out-of-Sync": True}
_HOUSEKEEPING = {"", "configure terminal", "configure", "exit", "end"}


def preview_entry(resp, serial):
    """The single legacy config-preview entry for a serial, from a dcnm_send response.
    Missing, ambiguous, malformed or self-inconsistent data raises PvlanError."""
    if not isinstance(resp, dict) or resp.get("RETURN_CODE") != 200:
        raise PvlanError("config-preview for %s did not answer 200" % serial)
    data = resp.get("DATA")
    if not isinstance(data, list):
        raise PvlanError("config-preview for %s returned no entry list" % serial)
    entries = [d for d in data if isinstance(d, dict) and d.get("switchId") == serial]
    if len(entries) != 1:
        raise PvlanError("config-preview returned %d entries for %s" % (len(entries), serial))
    entry = entries[0]
    pend = entry.get("pendingConfig")
    if not isinstance(pend, list) or not all(isinstance(l, str) for l in pend):
        raise PvlanError("config-preview pendingConfig for %s is missing or malformed" % serial)
    for key in ("runningConfig", "expectedConfig"):
        if key in entry and not (isinstance(entry[key], list) and all(isinstance(l, str) for l in entry[key])):
            raise PvlanError("config-preview %s for %s is malformed" % (key, serial))
    status = entry.get("status")
    if status not in LEGACY_PREVIEW_STATUS:
        raise PvlanError("config-preview status %r for %s is unknown" % (status, serial))
    if LEGACY_PREVIEW_STATUS[status] != bool(pend):
        raise PvlanError("config-preview status %r for %s is inconsistent with its pending" % (status, serial))
    return entry


def split_blocks(lines):
    """pendingConfig -> ({interface name lower: [body lines stripped]}, [global lines])."""
    blocks, global_lines, ctx = {}, [], None
    for raw in lines:
        stripped = raw.strip()
        if not raw.startswith(" "):
            if stripped.lower() in _HOUSEKEEPING:
                ctx = None
                continue
            m = re.match(r"^interface (\S+)$", stripped, re.IGNORECASE)
            if m:
                ctx = m.group(1).lower()
                blocks.setdefault(ctx, [])
            else:
                ctx = None
                global_lines.append(stripped)
        elif ctx is None:
            global_lines.append(stripped)
        elif stripped:
            blocks[ctx].append(stripped)
    return blocks, global_lines


def _bad_vlan_numbers(line):
    if "vlan" not in line and "private-vlan" not in line:
        return False
    for tok in line.split():
        if re.match(r"^[0-9][0-9,\-]*$", tok):
            parsed = _lenient_vlan_set(tok)
            if not parsed or any(not 1 <= v <= 4094 for v in parsed):
                return True
    return False


def _line_pairs(match):
    p = int(match.group(1))
    secondaries = _lenient_vlan_set(match.group(2))
    if not 1 <= p <= 4094 or not secondaries or any(not 1 <= v <= 4094 for v in secondaries):
        return None
    return {(p, s) for s in secondaries}


def validate_transition(body, pre, post, release=False):
    """Problems (empty = deployable) for one PVLAN target's fresh pending body lines, given the
    pre-write and post-write Models. Positive lines must belong to the post state; negations
    must withdraw an OWNED line of the pre state that the post state does not hold (a foreign
    pre line is never removable); every added or removed pair and every changed owned line must
    be visible. Foreign pre lines create no obligation."""
    problems = []
    if not (pre.modeled and post.modeled):
        return ["the transition from or to this policy is not modeled; deploy refused"]
    same_kind = pre.list_kind is not None and pre.list_kind == post.list_kind
    # Same list kind: every withdrawn pair must be visible. A list-kind change (submode change
    # or reset) only PERMITS withdrawal lines: the measured promiscuous -> trunk promiscuous
    # pending withdraws the old mapping through the mode change alone.
    removable = (pre.pairs - post.pairs) if same_kind else set(pre.pairs)
    required_removed = (pre.pairs - post.pairs) if same_kind else set()
    added_pairs = (post.pairs - pre.pairs) if same_kind else set(post.pairs)
    seen_pos, seen_neg, neg_scalars, pos_scalars = set(), set(), set(), set()
    for line in body:
        if _bad_vlan_numbers(line):
            problems.append("malformed VLAN number in %r" % line)
            continue
        if line in post.scalars:
            pos_scalars.add(line)
            continue
        # An owned NEGATIVE-form line (`no lldp transmit`, `no cdp enable`) is withdrawn on NX-OS by its positive form
        # (`lldp transmit`, `cdp enable`), never by `no no ...`. Accepted only for a `no X` line the pre state owns and the post
        # state no longer holds; the NX-OS form is a convention, NOT measured on a PVLAN interface.
        if not line.startswith("no ") and ("no " + line) in pre.scalars and ("no " + line) not in post.scalars:
            neg_scalars.add("no " + line)
            continue
        if line.startswith("no "):
            target = line[3:]
            if target in pre.foreign:
                problems.append(
                    "removal %r withdraws a device command the native PVLAN operation does not own; "
                    "its presence on the device does not authorize the removal" % line
                )
                continue
            if target in pre.scalars and target not in post.scalars:
                neg_scalars.add(target)
                continue
            m = _LIST_LINE.get(pre.list_kind).match(target) if pre.list_kind else None
            pairs = _line_pairs(m) if m else None
            if pairs and pairs <= removable:
                seen_neg |= pairs
                continue
            problems.append("unexpected removal %r" % line)
            continue
        m = _TRUNK_REMOVE.match(line)
        if m:
            pairs = _line_pairs(m)
            if (
                same_kind
                and post.list_kind == MODE_TRUNK_PROMISCUOUS
                and pairs
                and pairs <= removable
                and all(any(q == p for q, _qs in post.pairs) for p, _ps in pairs)
            ):
                seen_neg |= pairs
                continue
            problems.append("unexpected partial removal %r" % line)
            continue
        m = _LIST_LINE.get(post.list_kind).match(line) if post.list_kind else None
        if m:
            pairs = _line_pairs(m)
            if pairs and pairs <= post.pairs:
                seen_pos |= pairs
                continue
            problems.append("list line %r is not part of the intended state" % line)
            continue
        problems.append("unmodeled command %r" % line)
    # The bare `switchport` of the pre state is withdrawn by the
    # post state's own `no switchport` line (the measured pending carries no separate withdrawal of it); the PVLAN/channel-group lines of
    # the pre state still need their own withdrawals, as measured.
    if "no switchport" in pos_scalars and "switchport" in pre.scalars and "switchport" not in post.scalars:
        neg_scalars.add("switchport")
    # Measured (NDFC 12.6.0.267: a down member released up carries ONE `no shutdown` line in the pending): the post state's
    # own `no shutdown` withdraws the pre state's `shutdown`, exactly like `no switchport` above. ONLY for a member RELEASE (`release`): any
    # other shutdown -> no shutdown transition keeps the documented limit of this validator.
    if release and "no shutdown" in pos_scalars and "shutdown" in pre.scalars and "shutdown" not in post.scalars:
        neg_scalars.add("shutdown")
    missing_add = added_pairs - seen_pos
    if missing_add:
        problems.append("intended pair(s) %s are absent from the pending" % sorted(missing_add))
    missing_rm = required_removed - seen_neg
    if missing_rm:
        problems.append("withdrawn pair(s) %s are absent from the pending" % sorted(missing_rm))
    for line in sorted(post.scalars - pre.scalars - pos_scalars):
        problems.append("intended command %r is absent from the pending" % line)
    for line in sorted(pre.scalars - post.scalars - neg_scalars):
        problems.append("withdrawal of %r is absent from the pending" % line)
    return problems


# ------------------------------------------------------------------ controller authority
def classify_secondary(networks, vlan):
    """Type of the fabric network carrying secondary `vlan`, from measured legacy fields only
    (top-level `type`, parsed networkTemplateConfig `type` and `vlanId`). Returns
    ("isolated" | "community", None) or (None, reason). The VLAN number alone is never used."""
    found = []
    for net in networks or []:
        if not isinstance(net, dict):
            continue
        tc = net.get("networkTemplateConfig")
        if isinstance(tc, str):
            try:
                tc = json.loads(tc)
            except ValueError:
                tc = None
        if not isinstance(tc, dict):
            continue
        if str(tc.get("vlanId", "")).strip() == str(vlan):
            found.append((net, tc))
    if len(found) != 1:
        return None, "%d fabric networks carry VLAN %d; its secondary type cannot be established" % (len(found), vlan)
    net, tc = found[0]
    top = str(net.get("type") or "").strip().lower()
    inner = str(tc.get("type") or "").strip().lower()
    if not top or not inner or top != inner:
        return None, "network type for VLAN %d is missing or conflicting" % vlan
    if top in ("isolated", "community"):
        return top, None
    return None, "VLAN %d is a %r network, not a PVLAN secondary" % (vlan, top)


def template_declared_names(content):
    """Variable names declared in a template's '##template variables' section."""
    if not isinstance(content, str):
        return set()
    section = content.split("##template variables", 1)[-1].split("##template content", 1)[0]
    names = set(re.findall(r"^\s*(?:string|enum|boolean|integer|interface|long|ipV4Address|ipV6Address)\s+([A-Za-z_][A-Za-z0-9_]*)", section, re.M))
    names |= set(re.findall(r"\}\s*([A-Za-z_][A-Za-z0-9_]*)\[\]\s*;", section))
    return names


def modify_outcome_problems(resp, targets):
    """Per-target outcome of a legacy interface/modify batch. Every PVLAN target needs a
    SUCCESS item naming it; ERROR, a missing item, an unknown type or a malformed body is
    indeterminate and must stop before any deploy."""
    data = resp.get("DATA") if isinstance(resp, dict) else None
    if not isinstance(data, list) or not all(isinstance(i, dict) for i in data):
        return ["the modify response carries no per-item outcome list"]
    problems = []
    for sno, name in targets:
        names = {("%s~%s" % (sno, name)).lower(), ("%s:%s" % (sno, name)).lower()}
        items = [i for i in data if str(i.get("entity", "")).lower() in names]
        types = sorted({str(i.get("reportItemType", "")).upper() for i in items})
        if not items:
            problems.append("%s on %s: no outcome item" % (name, sno))
        elif types != ["SUCCESS"]:
            problems.append("%s on %s: outcome %s" % (name, sno, "/".join(types) or "<none>"))
    return problems


_BENIGN_DEPLOY = ("No Commands to execute", "In-Sync")
DEPLOY_SUCCESS_MESSAGE = "Interface deployed successfully"


def deploy_outcome(resp, items):
    """(problems, benign) for ONE interface deploy attempt, judged on the original response.
    `items` are the PVLAN targets of the attempt; each must be named by a success body (only a
    single-interface body was measured; naming several is an unmeasured generalization).

    Accepted bodies only:
      * measured success: HTTP 200, DATA {"message": "Interface deployed successfully",
        "value": [{"serialNumber", "IfName"}, ...]} naming every deployed interface;
      * documented benign notice (module source, not measured): HTTP 200, DATA a list
        whose items are all WARNING "No Commands to execute" / "In-Sync". The caller must still
        corroborate it with a fresh readback.
    Anything else -- any HTTP code but 200, ERROR in a dict or a list, an unknown key or shape,
    a success body that does not name the deployed interfaces -- is a failed or indeterminate
    attempt. A later In-Sync read never converts it into success."""
    if not isinstance(resp, dict):
        return ["deploy returned no response"], False
    if resp.get("RETURN_CODE") != 200:
        return ["deploy answered HTTP %s" % resp.get("RETURN_CODE")], False
    data = resp.get("DATA")
    wanted = {(str(i.get("serialNumber")), str(i.get("ifName", "")).lower()) for i in items}
    if isinstance(data, dict):
        if str(data.get("reportItemType", "")).upper() == "ERROR" or data.get("error"):
            return ["deploy reported an error: %s" % str(data.get("message") or data.get("error"))[:200]], False
        value = data.get("value")
        if set(data) != {"message", "value"} or data.get("message") != DEPLOY_SUCCESS_MESSAGE or not isinstance(value, list):
            return ["deploy response body is not a recognised success: keys %s" % sorted(data)], False
        named = set()
        for v in value:
            if not isinstance(v, dict) or not isinstance(v.get("serialNumber"), str) or not isinstance(v.get("IfName"), str):
                return ["deploy success body carries a malformed interface entry"], False
            named.add((v["serialNumber"], v["IfName"].lower()))
        missing = sorted(wanted - named)
        if missing:
            return ["deploy success body does not name %s" % ", ".join("%s on %s" % (n, s) for s, n in missing)], False
        return [], False
    if isinstance(data, list) and data:
        problems = []
        for item in data:
            kind = str(item.get("reportItemType", "")).upper() if isinstance(item, dict) else ""
            message = str(item.get("message", "")) if isinstance(item, dict) else ""
            if kind == "WARNING" and any(b in message for b in _BENIGN_DEPLOY):
                continue
            problems.append("deploy item %s: %s" % (kind or "<unknown>", message[:200]))
        return problems, not problems
    return ["deploy response body is not recognised"], False


# ------------------------------------------------------------------ device authority
def interface_stanza(lines, name):
    """(count, body) of `interface <name>` in a running/expected configuration list."""
    target = "interface " + name.lower()
    body, inside, count = [], False, 0
    for line in lines or []:
        if not line.startswith(" "):
            inside = line.strip().lower() == target
            count += inside
            continue
        if inside and line.strip() and not line.strip().startswith("!"):
            body.append(line.strip())
    return count, body


def running_po_members(lines, po_number):
    """(members, pc_mode) of port-channel `po_number` as the DEVICE holds it: every physical interface stanza of a running
    configuration whose body carries the persisted `channel-group N` (pc_mode "on") or `channel-group N mode M` line for that number.
    Names are returned as the running configuration spells them; pc_mode is None when no member, or the members disagree."""
    pattern = re.compile(r"^channel-group %s(?: mode (active|passive))?$" % re.escape(str(po_number)))
    members, modes, current = [], set(), None
    for line in lines or []:
        if not line.startswith(" "):
            m = re.match(r"^interface (\S+)$", line.strip(), re.I)
            current = m.group(1) if m and m.group(1).lower().startswith("ethernet") else None
            continue
        hit = pattern.match(line.strip()) if current else None
        if hit and current not in members:
            members.append(current)
            modes.add(hit.group(1) or "on")
    return sorted(members, key=str.lower), (modes.pop() if len(modes) == 1 else None)


def cli_model(body, vocabulary=None):
    """Model of an interface from device (runningConfig) or controller (expectedConfig) CLI.

    Every line is OBSERVED; only lines the transition's vocabulary owns become scalars or pairs
    (MODELED). The rest are kept apart as `foreign`: they are not removable and create no
    obligation. Defaults NX-OS omits are restored so it compares with render(): a
    'switchport mode ...' line implies 'switchport', and the absence of 'shutdown' means
    'no shutdown'. Without a vocabulary the union of the modeled policies is used."""
    vocabulary = vocabulary or DEFAULT_VOCABULARY
    owned = [line for line in body if vocabulary.owns(line)]
    foreign = [line for line in body if not vocabulary.owns(line)]
    kind = None
    for line in owned:
        m = re.match(r"^switchport mode private-vlan (.+)$", line)
        if m and m.group(1) in PVLAN_MODES:
            kind = m.group(1)
    scalars, pairs = set(), set()
    for line in owned:
        m = _LIST_LINE[kind].match(line) if kind else None
        found = _line_pairs(m) if m else None
        if found:
            pairs |= found
        else:
            scalars.add(line)
    if any(l.startswith("switchport mode") for l in owned):
        scalars.add("switchport")
    if "shutdown" not in scalars:
        scalars.add("no shutdown")
    return Model(scalars, kind, pairs, True, foreign)


def same_state(a, b):
    return a.modeled and b.modeled and a.scalars == b.scalars and a.list_kind == b.list_kind and a.pairs == b.pairs


def _difference(a, b):
    return {
        "missing": sorted(b.scalars - a.scalars) + ["pair %d/%d" % p for p in sorted(b.pairs - a.pairs)],
        "unexpected": sorted(a.scalars - b.scalars) + ["pair %d/%d" % p for p in sorted(a.pairs - b.pairs)],
    }


def assess_target(body, entry, name, desired, vocabulary=None, absent_ok=False, member_force=None, member_inherit=None,
                  member_reassert=None, member_mtu_inherit=None, member_speed_inherit=None, release=False):
    """Decision for one PVLAN target from ONE fresh preview entry.

    Authority, all from that entry: `runningConfig` (device), `expectedConfig` (controller
    intent) and the interface block of `pendingConfig`. `vocabulary` (transition_vocabulary of
    the requested transition) separates what the operation owns from what it only observes.
    Returns (decision, problems) with decision in {"converged", "deploy", "refuse"}:
      * refuse when either configuration is missing/ambiguous for the interface, the controller's
        expected configuration holds a command outside the vocabulary or disagrees with the
        intended state (stale intent or a recompute that did not take);
      * refuse when the device holds a command the operation does not own inside a field
        namespace it does own: the model cannot interpret it, so neither safety nor
        convergence can be proven;
      * converged when the block is empty AND the device's owned state is the intended state;
        foreign device commands outside the owned namespaces are left untouched;
      * refuse when the block is empty but the device's owned state differs;
      * otherwise the remaining work is validated as the transition device -> intended state, in
        which a foreign device command can never be withdrawn.
    `member_force` (port-channel member creation only) applies po_member_force_transition() first.
    `member_inherit` (the NAME of the port-channel of an existing member, given only when that port-channel's own pending
    changes) reads the member's device state through po_member_inherited_state() against the port-channel's running stanza
    in the same entry: an empty member pending is then a deploy carried by the parent, not a refusal.
    `member_reassert` (the {"po_number", "pc_mode"} of the port-channel of an EXISTING member) applies
    po_member_force_reassertion() before the empty-pending decision.
    `member_mtu_inherit` (the parent context of an EXISTING member of an updated regular port-channel) applies
    po_member_mtu_inherited_state(), the measured jumbo -> default withdrawal and the measured default -> jumbo addition only,
    before the empty-pending decision.
    `member_speed_inherit` (SP1: the same parent context) applies po_member_speed_inherited_state(), the DIAG-measured `speed 1000`
    addition and withdrawal carried by the port-channel's own pending, before the empty-pending decision; never together with an MTU
    inheritance (that combination is not measured). The same parameter also drives po_member_duplex_inherited_state() (a fixed `speed 1000`
    that does not change, `duplex full` added or withdrawn); it never runs in the same transition as the MTU or the speed rules."""
    if not desired.modeled:
        return "refuse", ["the intended state of %s is not modeled" % name]
    vocabulary = vocabulary or DEFAULT_VOCABULARY
    for key in ("runningConfig", "expectedConfig"):
        if not isinstance(entry.get(key), list):
            return "refuse", ["the fresh preview carries no %s, so the device state of %s is unknown" % (key, name)]
    rc, running = interface_stanza(entry["runningConfig"], name)
    xc, expected = interface_stanza(entry["expectedConfig"], name)
    if absent_ok and rc == 0 and xc == 1:
        # An interface that is created by this very operation has no running
        # stanza yet. That is accepted ONLY here, from a readable runningConfig list and exactly
        # one expected stanza; a duplicated or missing expected stanza is still a refusal.
        observed = Model((), None, (), True)
    elif rc != 1 or xc != 1:
        return "refuse", ["the fresh preview holds %d running and %d expected stanzas for %s" % (rc, xc, name)]
    else:
        observed = cli_model(running, vocabulary)
    controller = cli_model(expected, vocabulary)
    desired = adopt_capability_lines(desired, controller)
    if controller.foreign:
        return "refuse", [
            "the controller's expected configuration for %s holds command(s) outside the modeled "
            "contract of this transition: %s" % (name, sorted(controller.foreign))
        ]
    if not same_state(controller, desired):
        return "refuse", ["the controller's expected configuration for %s disagrees with the intended state: %s" % (name, _difference(controller, desired))]
    interfering = sorted(line for line in observed.foreign if vocabulary.interferes(line))
    if interfering:
        return "refuse", [
            "the device holds command(s) %s on %s in fields this operation owns but cannot "
            "interpret, so the transition cannot be proven safe or converged" % (interfering, name)
        ]
    inherited = False
    if member_inherit:
        prc, parent_running = interface_stanza(entry["runningConfig"], member_inherit)
        parent_observed = cli_model(parent_running, vocabulary) if prc == 1 else None
        observed, inherited = po_member_inherited_state(observed, desired, parent_observed)
    mtu_inherited = False
    if member_mtu_inherit:
        observed, mtu_inherited = po_member_mtu_inherited_state(entry, observed, desired, body, member_mtu_inherit)
        inherited = inherited or mtu_inherited
    speed_inherited = False
    if member_speed_inherit and not mtu_inherited:
        observed, speed_inherited = po_member_speed_inherited_state(entry, observed, desired, body, member_speed_inherit)
        inherited = inherited or speed_inherited
    if member_speed_inherit and not mtu_inherited and not speed_inherited:
        # DUPLEX (measured): the same parent context, never in the same transition as an MTU or a speed inheritance
        observed, duplex_inherited = po_member_duplex_inherited_state(entry, observed, desired, body, member_speed_inherit)
        inherited = inherited or duplex_inherited
    if member_reassert:
        body, problems = po_member_force_reassertion(body, observed, desired, member_reassert)
        if problems:
            return "refuse", problems
    if not body:
        if same_state(observed, desired):
            return ("deploy" if inherited else "converged"), []
        return "refuse", ["the pending for %s is empty but the device differs from the intended state: %s" % (name, _difference(observed, desired))]
    body, observed, problems = po_member_force_transition(body, observed, desired, member_force)
    if problems:
        return "refuse", problems
    problems = validate_transition(body, observed, desired, release=release)
    return ("refuse", problems) if problems else ("deploy", [])


# ------------------------------------------------------------------ interface summary policy
# MEASURED (NDFC 12.6.0.267, interface/detail, 72 entries): no entry carries a top-level `policy`;
# every Ethernet entry carries `underlayPolicies` as a list with ONE object holding (among others)
# templateName, policyId, source, entityName, entityType and serialNumber; policy-less SVIs carry null.
SUMMARY_POLICY_KEYS = ("templateName", "policyId", "source", "entityName", "entityType", "serialNumber")
SUMMARY_KNOWN = "known"
SUMMARY_ABSENT = "absent"
SUMMARY_UNKNOWN = "unknown"


def summary_policy(entry, ifname):
    """Classify the policy an interface summary entry reports for `ifname`: (state, value).

    known   -> value is the underlay object reduced to SUMMARY_POLICY_KEYS (all strings, entity and
               serial the entry's own). A top-level `policy` is optional; when present it must equal
               the underlay templateName, otherwise the answer is contradictory (unknown).
    absent  -> the summary demonstrates that no policy exists: underlayPolicies null or empty and no
               top-level policy. value is None.
    unknown -> anything else (missing list, another container, several objects, missing or non-string
               keys, wrong entity, contradiction). value is the reason. Never read as "no policy"."""
    if not isinstance(entry, dict):
        return SUMMARY_UNKNOWN, "the interface summary entry is not an object"
    top = entry.get("policy")
    if "underlayPolicies" not in entry:
        return SUMMARY_UNKNOWN, "the interface summary carries no underlay policy list (absent), so ownership is unknown"
    under = entry["underlayPolicies"]
    if under is None or under == []:
        if top is not None:
            return SUMMARY_UNKNOWN, "the summary policy %r has no underlay policy, so the two disagree" % (top,)
        return SUMMARY_ABSENT, None
    if not isinstance(under, list):
        return SUMMARY_UNKNOWN, "the interface summary carries no underlay policy list (%s), so ownership is unknown" % type(under).__name__
    if len(under) != 1 or not isinstance(under[0], dict):
        return SUMMARY_UNKNOWN, "the interface summary lists %d underlay policies; exactly one direct policy is required" % len(under)
    u = under[0]
    source = u.get("source")
    if not isinstance(source, str):
        return SUMMARY_UNKNOWN, "the underlay policy has no source string, so ownership is unknown"
    missing = [k for k in SUMMARY_POLICY_KEYS if not isinstance(u.get(k), str) or (k != "source" and not u.get(k))]
    if missing:
        if source:
            return SUMMARY_UNKNOWN, "its policy is owned by another resource (source %s)" % source
        return SUMMARY_UNKNOWN, "the underlay policy lacks %s, so its identity is unknown" % ", ".join(missing)
    if u["entityName"].lower() != str(ifname).lower() or u["serialNumber"] != entry.get("serialNo"):
        return SUMMARY_UNKNOWN, "the underlay policy targets %s on %s, not this interface" % (u["entityName"], u["serialNumber"])
    if u["entityType"].upper() != "INTERFACE":
        return SUMMARY_UNKNOWN, "the underlay policy is attached to a %s, not to the interface" % u["entityType"]
    if top is not None and top != u["templateName"]:
        return SUMMARY_UNKNOWN, "the summary policy %r contradicts the underlay policy %r" % (top, u["templateName"])
    return SUMMARY_KNOWN, dict((k, u[k]) for k in SUMMARY_POLICY_KEYS)


def summary_mentions_policy(entry, policy):
    """Whether any policy field of a summary entry (top-level or an underlay object) names `policy`,
    whatever the entry's validity. Used so that an unreadable entry is never taken for another policy."""
    if not isinstance(entry, dict):
        return False
    if entry.get("policy") == policy:
        return True
    under = entry.get("underlayPolicies")
    items = under if isinstance(under, list) else [under] if isinstance(under, dict) else []
    return any(isinstance(u, dict) and u.get("templateName") == policy for u in items)


# ================================================================== regular port-channel, four PVLAN modes
# Everything below is derived from the
# captured templates int_port_channel_pvlan_host / int_port_channel_pvlan_member (their template contract and
# the port-channel validation contract) and from the helpers above; no value comes from a controller measurement of a
# port-channel. Scope (anything else is refused before a write): ONE port-channel with exactly ONE physical member;
# creation; update of the PVLAN lists/scalars without changing pvlan_mode or the member; identical repetition.
# NATIVE_EXTEND + the declarative LACP rows: companions the PVLAN helper keeps owning, with the public key
# the regular port-channel spec already uses for the same nvPair. Every one is declared by int_port_channel_pvlan_host and rendered
# by its add() (Po body) or handed to the member (member body / Inherited Commands).
PO_NATIVE_COMPANIONS = (
    ("bpdu_guard", "BPDUGUARD_ENABLED", "bpdu"),
    ("port_type_fast", "PORTTYPE_FAST_ENABLED", "bool"),
    ("mtu", "MTU", "mtu"),
    ("copy_description", "COPY_DESC", "bool"),
    ("enable_cdp", "CDP_ENABLE", "bool"),
    ("orphan_port", "ENABLE_ORPHAN_PORT", "bool"),
    ("duplex", "PORT_DUPLEX_MODE", "duplex"),
    ("queuing_policy", "QUEUING_POLICY", "policy"),
    ("disable_lacp_suspend_individual", "DISABLE_LACP_SUSPEND", "bool"),
    ("lacp_port_priority", "LACP_PORT_PRIO", "lacp_prio"),
    ("lacp_rate", "LACP_RATE", "lacp_rate"),
    # RC1: SPEED (HOST 59 enum, 292-296 support check, 464-471 render, 517-521 inherited by every member).
    ("speed", "SPEED", "speed"),
)
# Registry companions of the port-channel parent (lldp x2, spanning_tree_port_type, disable_queuing_stats).
PO_REGISTRY_KEYS = frozenset(registered_profile_keys(PO_HOST_POLICY))
PO_PROFILE_KEYS = frozenset((
    "mode", "pvlan_mode", "pvlan_association", "pvlan_mapping", "native_vlan", "allowed_vlans",
    "members", "pc_mode", "description", "admin_state",
    # RC1: freeform commands of the port-channel (CONF), the regular port-channel's public key.
    "cmds",
) + tuple(c[0] for c in PO_NATIVE_COMPANIONS)) | PO_REGISTRY_KEYS
# RC1: interface_utility.findInheritedCommandsInPOFF (captured, HELPERS-READ-1) copies every freeform line that starts with one of these
# words, plus the sub-commands of `cts`, to the 'Inherited Commands' child of EVERY member. Such a line is refused in a port-channel or vPC
# freeform: it would configure the members outside their modeled state.
PO_FREEFORM_INHERITED_PREFIXES = ("cts", "duplex", "flowcontrol", "load-interval", "medium", "mtu", "no negotiate", "port-type",
                                  "priority-flow-control", "speed", "storm-control", "switchport")
# RC1: command words a structured field (or the aggregate's identity) owns on the port-channel / vPC child; a freeform line in them,
# positive or `no`, is refused so the freeform never competes with the modeled state.
PO_FREEFORM_RESERVED = ("switchport", "private-vlan", "channel-group", "vpc", "interface", "mtu", "speed", "negotiate", "duplex",
                        "spanning-tree", "description", "cdp", "lldp", "lacp", "shutdown", "priority-flow-control", "service-policy",
                        "ip port access-group")


def po_freeform_errors(key, value):
    """RC1: raw validation of a port-channel / vPC freeform list (`cmds`, `peerN_cmds`): one top-level command per entry, none that the
    controller would copy to the members, none in a field a structured key owns. The message names the field, never a whole command.
    A text (how NaC renders freeform_config) and list entries holding line breaks are checked line by line (cmds_lines, indentation kept);
    the index is the line's position after that split. A text with a comma is refused, as for Ethernet."""
    lines = cmds_lines(value)
    if lines is None:
        if isinstance(value, str):
            return ["%s given as text must not contain a comma; use a list of strings" % key]
        return ["%s must be a list of strings (or a text with one command per line)" % key]
    errors = []
    for index, line in enumerate(lines):
        where = "%s[%d]" % (key, index)
        if not line.strip():
            errors.append("%s is empty" % where)
            continue
        if line != line.lstrip():
            errors.append("%s is an indented sub-command; sub-mode blocks are not modeled in a port-channel freeform" % where)
            continue
        low = line.strip().lower()
        if any(low.startswith(p) for p in PO_FREEFORM_INHERITED_PREFIXES):
            errors.append("%s starts with a command the controller copies to every member (findInheritedCommandsInPOFF); "
                          "use the structured field or configure it outside the port-channel" % where)
            continue
        bare = low[3:].lstrip() if low.startswith("no ") else low
        word = next((w for w in PO_FREEFORM_RESERVED if bare == w or bare.startswith(w + " ")), None)
        if word:
            errors.append("%s is a '%s' command, owned by a structured field of the port-channel; use that field" % (where, word))
    return errors


def freeform_lines(text):
    """RC1: the freeform commands of a stored CONF text, in order, without blank lines."""
    return [line.strip() for line in str(text or "").split("\n") if line.strip()]


def stored_freeform_errors(key, text):
    """RC1: po_freeform_errors of a STORED CONF text, line by line with its own indentation kept (an indented sub-command stored by
    another tool is refused, not flattened into a top-level command)."""
    return po_freeform_errors(key, [line.rstrip() for line in str(text or "").split("\n") if line.strip()])


def freeform_request(cmds):
    """the commands of ONE freeform request, stripped, with exact duplicates dropped and the order of first appearance kept, so a
    repeated entry is never stored twice (an idempotency comparison that counts lines would otherwise see a change on every run).
    A text or a list entry holding line breaks contributes its lines (cmds_lines); a text is never iterated character by character."""
    if cmds is None:
        return []
    lines = cmds_lines(cmds)
    if lines is None:
        raise PvlanError("freeform commands must be a list of strings or a text without a comma")
    out = []
    for line in lines:
        text = line.strip()
        # A blank line is never a command: validation refuses one in a list, and the empty text (NaC's omitted freeform_config) reaches
        # the builders as [""] through Ansible's list conversion.
        if text and text not in out:
            out.append(text)
    return out


def freeform_merged(have_text, requested):
    """RC1: `merged` rule of the PVLAN freeform (the Ethernet `cmds` precedent): HAVE's lines kept in their order, the requested lines
    HAVE does not hold appended (each once); with nothing new HAVE's own text is returned unchanged."""
    have_lines = freeform_lines(have_text)
    extra = [line for line in freeform_request(requested) if line not in have_lines]
    return "\n".join(have_lines + extra) if extra else (have_text or "")


def _freeform_same(have_text, want_text):
    """RC1: two CONF texts hold the same commands (order and blank lines ignored, as dcnm_intf_compare_elements compares CONF)."""
    return sorted(freeform_lines(have_text)) == sorted(freeform_lines(want_text))


PO_PC_MODES = ("on", "active", "passive")
# Template declarations (host template, "##template variables"), in wire form.
PO_TEMPLATE_DEFAULTS = (
    ("PC_MODE", "active"),
    ("BPDUGUARD_ENABLED", "true"),
    ("PORTTYPE_FAST_ENABLED", "true"),
    ("spanningTreePortType", "no"),
    ("MTU", "jumbo"),
    ("SPEED", "Auto"),
    ("COPY_DESC", "false"),
    ("CDP_ENABLE", "true"),
    ("lldpTransmit", "false"),
    ("lldpReceive", "false"),
    ("ENABLE_ORPHAN_PORT", "false"),
    ("PORT_DUPLEX_MODE", "auto"),
    ("DISABLE_LACP_SUSPEND", "false"),
    ("LACP_PORT_PRIO", 32768),  # declared `integer`: sent as an integer, not as a string (UNMEASURED)
    ("LACP_RATE", "normal"),
    ("QUEUING_POLICY", ""),
    ("queuingStats", "false"),
    ("ADMIN_STATE", "true"),
)
# PVLAN_NATIVE_VLAN is declared `integer` 1-4094 on BOTH the Ethernet and the port-channel template.
# Neutral value: the empty string. A non-empty native VLAN is sent as a string of digits, the form MEASURED as
# accepted for the integer-declared Ethernet field over the same legacy transport (measured). Whether the port-channel
# create/modify path accepts it, and how it reads it back, is NOT measured: to be measured with the trunk roles.
PO_NATIVE_NEUTRAL = ""
PO_NAME = re.compile(r"^port-channel[1-9][0-9]{0,3}$", re.IGNORECASE)
PO_PHYSICAL_MEMBER = re.compile(r"^ethernet[0-9]+/[0-9]+$", re.IGNORECASE)
# Every nvPair the host template declares (29) plus the bookkeeping keys the controller adds.
PO_KNOWN_HAVE_NVPAIRS = frozenset(
    tuple(k for k, _d in PO_TEMPLATE_DEFAULTS)
    + ("SERIAL_NUMBER", "PO_ID", "MEMBER_INTERFACES", "DESC", "CONF", "PTP", "PVLAN_MODE", ALLOWED_VLANS, NATIVE_VLAN,
       MAPPING_LIST, ASSOCIATION_LIST, "INTF_NAME")
    + BOOKKEEPING
)
_PO_SCALAR_KEYS = frozenset(k for k, _d in PO_TEMPLATE_DEFAULTS) | frozenset(("DESC", "CONF"))
_PO_BOOL_KEYS = ("ADMIN_STATE", "BPDUGUARD_ENABLED", "PORTTYPE_FAST_ENABLED", "COPY_DESC", "CDP_ENABLE", "lldpTransmit",
                 "lldpReceive", "ENABLE_ORPHAN_PORT", "DISABLE_LACP_SUSPEND", "queuingStats")


def po_not_implemented(profile):
    """Reasons a port-channel PVLAN request is outside the first delivery (empty = in scope).
    Decided from the RAW profile, before any default or coercion and before any read. Requirements that depend on
    the current state (a creation needs `members` and the active list) are decided by reconcile_po()."""
    reasons = []
    if not isinstance(profile, dict):
        return ["profile must be a dictionary"]
    unknown = sorted(k for k in profile if k not in PO_PROFILE_KEYS and k not in INJECTED_KEYS)
    if unknown:
        reasons.append(
            "field(s) not implemented for a port-channel in mode 'pvlan': %s" % ", ".join(unknown))
    for key in sorted(k for k in profile if k in PO_PROFILE_KEYS):
        if profile[key] is None:
            reasons.append("%s must not be null" % key)
    mode = profile.get("pvlan_mode")
    if "pvlan_mode" not in profile:
        reasons.append("pvlan_mode is required for mode 'pvlan'")
        return reasons
    if mode not in PVLAN_MODES:
        reasons.append("pvlan_mode must be one of: %s" % ", ".join(PVLAN_MODES))
        return reasons
    if "members" in profile and profile["members"] is not None:
        members = profile["members"]
        reasons += member_list_errors(members, "members")
    pairs = []
    for field, allowed_modes in (("pvlan_association", ASSOCIATION_MODES), ("pvlan_mapping", MAPPING_MODES)):
        if field not in profile or profile[field] is None:
            continue
        if mode not in allowed_modes:
            reasons.append("%s is not valid for pvlan_mode '%s'" % (field, mode))
            continue
        try:
            pairs = requested_pairs(field, profile[field])
        except PvlanError as exc:
            reasons.append(str(exc))
    reasons += limit_errors(mode, pairs)
    for key in ("native_vlan", "allowed_vlans"):
        if key in profile and profile[key] is not None and mode not in TRUNK_MODES:
            reasons.append("%s is valid only for pvlan_mode trunk promiscuous or trunk secondary" % key)
    native = profile.get("native_vlan")
    if native is not None:
        if not isinstance(native, str):
            reasons.append("native_vlan must be a string")
        elif native != "" and (not re.match(r"^[1-9][0-9]{0,3}$", native) or not 1 <= int(native) <= 4094):
            reasons.append("native_vlan must be '' or one VLAN ID 1-4094")
    allowed = profile.get("allowed_vlans")
    if allowed is not None:
        if not isinstance(allowed, str):
            reasons.append("allowed_vlans must be a string")
        elif allowed.strip().lower() == "all":
            reasons.append("allowed_vlans 'all' is refused by int_port_channel_pvlan_host; give explicit ranges")
        elif allowed not in ("", "none"):
            try:
                vlan_set(allowed, "allowed_vlans")
            except PvlanError as exc:
                reasons.append(str(exc))
    pc_mode = profile.get("pc_mode")
    if pc_mode is not None and pc_mode not in PO_PC_MODES:
        reasons.append("pc_mode must be one of: %s" % ", ".join(PO_PC_MODES))
    if "description" in profile and profile["description"] is not None:
        desc = profile["description"]
        if not isinstance(desc, str) or not 1 <= len(desc) <= 254 or "\n" in desc:
            reasons.append("description must be a single-line string of 1-254 characters")
    if "admin_state" in profile and profile["admin_state"] is not None and not isinstance(profile["admin_state"], bool):
        reasons.append("admin_state must be a boolean")
    reasons += native_companion_errors(profile, PO_NATIVE_COMPANIONS)
    if profile.get("cmds") is not None:
        reasons += po_freeform_errors("cmds", profile["cmds"])
    reasons += registry_companion_errors(PO_HOST_POLICY, profile)
    return reasons


def _speed_duplex_token(nv, key, auto):
    """Normalized SPEED / PORT_DUPLEX_MODE of an nvPairs dict; a missing, empty or null value is the template default (auto)."""
    value = (nv or {}).get(key)
    value = auto if value is None or str(value).strip() == "" else str(value).strip().lower()
    return value


def speed_duplex_combined_change(have_nv, nv):
    """True when the transition HAVE -> final intent changes the SPEED and the PORT_DUPLEX_MODE of an EXISTING port-channel / vPC at once.
    Restating an equal value is not a change. That combined transition is not measured (the inheritance rules cover a duplex change over a
    fixed, unchanged speed 1000, or a speed change alone) and the gate would refuse it only AFTER the intent was written."""
    if have_nv is None:
        return False
    return (_speed_duplex_token(have_nv, "SPEED", "auto") != _speed_duplex_token(nv, "SPEED", "auto")
            and _speed_duplex_token(have_nv, "PORT_DUPLEX_MODE", "auto") != _speed_duplex_token(nv, "PORT_DUPLEX_MODE", "auto"))


SPEED_DUPLEX_COMBINED_MESSAGE = (
    "speed and duplex cannot change in the same request on an existing port-channel or vPC (that combined transition is not measured): "
    "set the fixed speed first, in its own request, and then the duplex; to withdraw both, set duplex auto first and then speed Auto "
    "(a creation may set both)")


def companion_state_problems(nv, raw, have_nv=None):
    """Template rules that depend on the RESULTING parent state, checked before any write on every create/update:
      * HOST:345-350 / vPC HOST:300-305 / POVPC rule: a spanning-tree port type network|normal is REJECTED while port type fast is
        true (the template returns an error instead of a configuration);
      * queuingStats only appends ` no-stats` to the queuing service-policy line (IsShow QUEUING_POLICY!=''): an EXPLICIT
        disable_queuing_stats true with no resulting queuing policy would be accepted and then ignored, so it is refused."""
    problems = []
    stp = str(nv.get("spanningTreePortType", "no") or "no").strip()
    if stp not in ("", "no") and str(nv.get("PORTTYPE_FAST_ENABLED", "true")).strip().lower() == "true":
        problems.append("spanning_tree_port_type '%s' is rejected by the template while port_type_fast is true; set port_type_fast "
                        "false in the same request" % stp)
    # Measured (on a port-channel: NX-OS rejects `duplex full` with speed Auto, "Duplex is not Compatible with Speed"): the FINAL
    # intent (merged resolves an omitted speed from HAVE, so omitting speed is not Auto when HAVE is fixed) may not ask a duplex other
    # than auto while the speed is Auto. A withdrawal towards auto, and a fixed speed, are untouched. Port-channel and vPC PVLAN only.
    duplex_final = str(nv.get("PORT_DUPLEX_MODE", "auto") or "auto").strip().lower()
    speed_final = str(nv.get("SPEED", "Auto") or "Auto").strip().lower()
    if duplex_final != "auto" and speed_final == "auto":
        problems.append("duplex '%s' needs a fixed speed: the device rejects it while the speed is Auto (the resulting intent has speed Auto); "
                        "%s" % (duplex_final, "set the fixed speed first, in its own request, and then the duplex" if have_nv is not None
                                else "a creation may set speed and duplex together, or keep duplex auto"))
    # An EXISTING port-channel / vPC whose SPEED and PORT_DUPLEX_MODE both change is refused before the write (the gate would refuse it
    # after the intent was written). Judged on HAVE -> final intent: restating an equal value is no change; a withdrawal of duplex alone passes.
    if speed_duplex_combined_change(have_nv, nv):
        problems.append(SPEED_DUPLEX_COMBINED_MESSAGE)
    if raw.get("disable_queuing_stats") is True and not str(nv.get("QUEUING_POLICY", "") or "").strip():
        problems.append("disable_queuing_stats true only takes effect with a queuing_policy (the template appends ' no-stats' to "
                        "that line); set queuing_policy in the same request")
    # vPC PVLAN ingress QoS, only on a parent that carries ENABLE_QOS: the regular contract ("qos_policy is only valid when
    # enable_qos is true"; IsShow ENABLE_QOS==true on QOS_POLICY and qosStatsSuppressed) checked on the RESULTING state.
    if "ENABLE_QOS" in nv:
        enabled = str(nv.get("ENABLE_QOS", "false")).strip().lower() == "true"
        policy = str(nv.get("QOS_POLICY", "") or "").strip()
        if raw.get("qos_policy") and not enabled:
            problems.append("qos_policy requires enable_qos true (the template ignores the policy while QoS is disabled); set "
                            "enable_qos true in the same request or remove qos_policy")
        if enabled and not policy:
            problems.append("enable_qos true needs a qos_policy: without one the template falls back to a fabric-dependent default "
                            "(QOS_CLASSIFICATION on an AI/ML fabric, nothing otherwise) that this module does not read; give the "
                            "policy-map explicitly")
        if raw.get("disable_qos_stats") is True and not (enabled and policy):
            problems.append("disable_qos_stats true only takes effect with enable_qos true and a qos_policy (the template appends "
                            "' no-stats' to that line); set them in the same request")
    return problems


def vpc_qos_normalize(nv, raw, full):
    """The regular rule, as the reference tests measure it on the regular vPC parents: a FULL payload (creation / replaced) with
    QoS disabled sends QOS_POLICY '' (dcnm_intf_get_vpc_payload); a merged request keeps an omitted QOS_POLICY from HAVE even when it
    disables QoS (dcnm_intf_compare_elements copies HAVE for an omitted key), so `full` is False there and nothing is cleared. The
    children never see a residual policy: the corrected parent hands QOS_POLICY only with ENABLE_QOS true."""
    if full and str(nv.get("ENABLE_QOS", "false")).strip().lower() != "true":
        nv["QOS_POLICY"] = ""
    return nv


def po_members(profile):
    return [m.strip() for m in profile.get("members") or []]


def _po_list_field(mode):
    return "pvlan_association" if active_list_key(mode) == ASSOCIATION_LIST else "pvlan_mapping"


def po_host_nvpairs(raw, ifname, members=None):
    """The EXPLICIT payload of int_port_channel_pvlan_host (D2), for a creation or a `replaced` update. Every value is
    the template's own declaration or the operator's input, in the template's declared type; nothing is copied from
    another Po policy. `raw` has already passed po_not_implemented(). `members` (wire text) overrides raw members."""
    mode = raw["pvlan_mode"]
    nv = {"PO_ID": ifname, "MEMBER_INTERFACES": members if members is not None else ",".join(po_members(raw))}
    for key, default in PO_TEMPLATE_DEFAULTS:
        nv[key] = default
    if raw.get("pc_mode") is not None:
        nv["PC_MODE"] = raw["pc_mode"]
    nv["DESC"] = raw["description"] if raw.get("description") is not None else ""
    if raw.get("admin_state") is not None:
        nv["ADMIN_STATE"] = "true" if raw["admin_state"] else "false"
    nv["CONF"] = "\n".join(freeform_request(raw["cmds"])) if raw.get("cmds") is not None else ""
    nv["PVLAN_MODE"] = mode
    trunk = mode in TRUNK_MODES
    nv[ALLOWED_VLANS] = raw.get("allowed_vlans", "") if trunk else ""
    nv[NATIVE_VLAN] = raw.get("native_vlan", PO_NATIVE_NEUTRAL) if trunk else PO_NATIVE_NEUTRAL
    active = active_list_key(mode)
    field = _po_list_field(mode)
    pairs = requested_pairs(field, raw[field]) if raw.get(field) is not None else []
    nv[MAPPING_LIST] = pairs_to_wire(MAPPING_LIST, pairs) if active == MAPPING_LIST and pairs else ""
    nv[ASSOCIATION_LIST] = pairs_to_wire(ASSOCIATION_LIST, pairs) if active == ASSOCIATION_LIST and pairs else ""
    # An explicit native companion replaces its template declaration; the registry companions are added by the caller
    # (reconcile_po / the payload builder), never here.
    apply_native_companions(nv, raw, PO_NATIVE_COMPANIONS)
    return nv


def _po_norm(key, value):
    """Comparable form of one HAVE/WANT nvPair of the port-channel host policy."""
    if value is None:
        return None
    text = str(value).strip()
    if key in _PO_BOOL_KEYS or key == "PORT_DUPLEX_MODE":
        return text.lower()
    if key == "MEMBER_INTERFACES":
        # Measured: a port-channel created through Manage stores its member as `e1/8`, the legacy path as
        # `Ethernet1/8`. Both name the same port; a token that is not one explicit port stays as written (never equal to a port).
        return tuple(sorted(set(po_member_canonical(m) or m.strip().lower() for m in re.split(r"[\n,]", text) if m.strip())))
    if key == "PO_ID":
        return text.lower()
    return text


def _po_same(key, have_value, want_value):
    if key == "CONF":
        return _freeform_same(have_value, want_value)
    if key in (MAPPING_LIST, ASSOCIATION_LIST):
        return pairs_from_wire(have_value or "", key) == pairs_from_wire(want_value or "", key)
    if key == NATIVE_VLAN:
        return native_equal(have_value or "", want_value or "")
    if key == ALLOWED_VLANS:
        return allowed_equal(have_value or "", want_value or "")
    return _po_norm(key, have_value) == _po_norm(key, want_value)


_PO_ABSENT_DEFAULT = dict(list(PO_TEMPLATE_DEFAULTS) + [
    ("DESC", ""), ("CONF", ""), (ALLOWED_VLANS, ""), (NATIVE_VLAN, ""), (MAPPING_LIST, ""), (ASSOCIATION_LIST, "")])


def member_list_update(state, have_text, requested):
    """MM-B: (wire text, added, removed) of the member list of an EXISTING aggregate under the regular port-channel rule. `requested` is
    the playbook list (None = omitted). merged: HAVE plus the requested members not in it (HAVE's own spelling and order kept, new
    members appended in the request's spelling); omitted -> HAVE unchanged. replaced/overridden: exactly the requested members (a kept
    member keeps HAVE's spelling); omitted or empty -> (None, [], []), refused by the caller. added/removed are canonical lower-case
    names (normalize_member_list); identity is by canonical port, so a reorder or an alias is not a change."""
    have_tokens = [t.strip() for t in re.split(r"[\n,]", "" if have_text is None else str(have_text)) if t.strip()]
    have_by = dict((po_member_canonical(t) or t.lower(), t) for t in have_tokens)
    if requested is None:
        if state in ("replaced", "overridden"):
            return None, [], []
        return have_text, [], []
    req_tokens = [str(t).strip() for t in requested if str(t).strip()]
    if not req_tokens and state in ("replaced", "overridden"):
        return None, [], []
    req_by = []
    for t in req_tokens:
        key = po_member_canonical(t) or t.lower()
        if key not in [k for k, _t in req_by]:
            req_by.append((key, t))
    if state in ("replaced", "overridden"):
        tokens = [have_by.get(k, t) for k, t in req_by]
        keys = [k for k, _t in req_by]
    else:
        tokens = list(have_tokens) + [t for k, t in req_by if k not in have_by]
        keys = list(have_by) + [k for k, _t in req_by if k not in have_by]
    added = sorted(k for k in keys if k not in have_by)
    removed = sorted(k for k in have_by if k not in keys)
    if not added and not removed:
        return have_text, [], []
    return ",".join(tokens), added, removed


def reconcile_po(state, raw, ifname, have_policy, have_nv, ndfc_version=None, patch_version=None):
    """Decision for ONE port-channel host WANT against its HAVE:
    {nv, update, creates, changed, blocked, new_secondaries, members}.

    The native companions (PO_NATIVE_COMPANIONS) follow the same merged/replaced rule as the other scalars; the
    registry companions follow registry_companions() (ndfc_version/patch_version are used for them only).

      * HAVE absent (have_policy None) -> creation with the explicit payload (members and the active list required);
      * HAVE is this policy, same pvlan_mode, same member set -> update:
          - `merged`: every omitted field keeps its HAVE value; the active list is the UNION of HAVE and request;
          - `replaced`: the explicit payload (omitted fields = template declarations), members kept from HAVE;
        equality (normalized) is a no-op returning the HAVE nvPairs untouched;
      * a change of pvlan_mode or of the member set, another policy, unclassifiable HAVE fields -> refused.
    The promiscuous partial-removal guard of the Ethernet path applies unchanged: on a port-channel its controller
    behaviour is NOT measured, so the protection is kept rather than assumed unnecessary (contract)."""
    out = {"nv": None, "update": False, "creates": False, "changed": {}, "blocked": [], "new_secondaries": [], "members": None,
           "added": [], "removed": []}
    mode = raw["pvlan_mode"]
    field = _po_list_field(mode)
    active = active_list_key(mode)
    if have_policy is None:
        if not po_members(raw):
            out["blocked"].append("members is required to create a port-channel: one or more existing physical members")
        if raw.get(field) is None or not requested_pairs(field, raw[field]):
            out["blocked"].append("%s is required to create a port-channel in pvlan_mode %s" % (field, mode))
        if out["blocked"]:
            return out
        nv = po_host_nvpairs(raw, ifname)
        reg_values, reg_blocked = registry_companions(state, PO_HOST_POLICY, raw, None, ndfc_version, patch_version)
        nv.update(reg_values)
        out["blocked"] += reg_blocked + companion_state_problems(nv, raw)
        if out["blocked"]:
            return out
        out.update(nv=nv, creates=True, changed=dict(nv), members=nv["MEMBER_INTERFACES"])
        if mode == MODE_TRUNK_SECONDARY:
            out["new_secondaries"] = sorted(pairs_from_wire(nv[ASSOCIATION_LIST], ASSOCIATION_LIST))
        return out
    if have_policy != PO_HOST_POLICY:
        out["blocked"].append(
            "the port-channel already holds policy %s; converting it to int_port_channel_pvlan_host is not "
            "implemented" % have_policy)
        return out
    if not isinstance(have_nv, dict):
        out["blocked"].append("the controller returned no nvPairs for the existing port-channel")
        return out
    have_mode = have_nv.get("PVLAN_MODE")
    if have_mode not in PVLAN_MODES:
        out["blocked"].append("current PVLAN_MODE %r is not a known int_port_channel_pvlan_host mode" % (have_mode,))
        return out
    if have_mode != mode:
        out["blocked"].append(
            "changing pvlan_mode of an existing port-channel (%r -> %r) is not implemented" % (have_mode, mode))
    lost = sorted(k for k in have_nv if k not in PO_KNOWN_HAVE_NVPAIRS and have_nv[k] not in ("", None))
    if lost:
        out["blocked"].append(
            "the port-channel holds nvPair(s) this module cannot classify and a full-set update could clear: %s"
            % ", ".join(lost))
    names, unresolved = normalize_member_list(have_nv.get("MEMBER_INTERFACES"))
    if not names or unresolved:
        out["blocked"].append("the existing port-channel needs a readable, non-empty list of explicit physical members")
    # MM-B: membership of an EXISTING port-channel follows the regular port-channel rule (dcnm_intf_compare_elements /
    # dcnm_intf_merge_want_and_have): `merged` is the union of HAVE and the requested members (an omitted `members` keeps HAVE);
    # `replaced`/`overridden` state the exact requested membership. An omitted or empty `members` there would remove every member, and
    # an empty member list is not implemented: refused, never read as "keep".
    members_text, added, removed = member_list_update(state, have_nv.get("MEMBER_INTERFACES", ""), raw.get("members"))
    if members_text is None:
        out["blocked"].append(
            "%s states the exact member list of an existing PVLAN port-channel: an omitted or empty `members` would remove every "
            "member, and an empty member list is not implemented; list the members explicitly" % state)
    if out["blocked"]:
        return out
    out["added"], out["removed"] = added, removed
    merged = state == "merged"
    current = pairs_from_wire(have_nv.get(active, "") or "", active)
    requested = requested_pairs(field, raw[field]) if raw.get(field) is not None else None
    desired_pairs = sorted(set(current) | set(requested or [])) if merged else sorted(set(requested or []))
    out["blocked"] += limit_errors(mode, desired_pairs)
    if promiscuous_partial_removal(have_mode, mode, current, desired_pairs):
        out["blocked"].append(
            "removing secondary VLAN(s) %s from a promiscuous mapping that keeps other secondaries is blocked "
            "(protection kept from the measured Ethernet defect; its behaviour on a port-channel is NOT measured). "
            "Remove the whole port-channel instead" % ", ".join("%d/%d" % p for p in sorted(set(current) - set(desired_pairs))))
    if out["blocked"]:
        return out
    if merged:
        nv = dict((k, v) for k, v in have_nv.items() if k in PO_KNOWN_HAVE_NVPAIRS and k not in BOOKKEEPING)
        for key, default in PO_TEMPLATE_DEFAULTS:
            nv.setdefault(key, default)
        nv.setdefault("DESC", "")
        nv.setdefault("CONF", "")
        if raw.get("pc_mode") is not None:
            nv["PC_MODE"] = raw["pc_mode"]
        if raw.get("description") is not None:
            nv["DESC"] = raw["description"]
        if raw.get("admin_state") is not None:
            nv["ADMIN_STATE"] = "true" if raw["admin_state"] else "false"
        if mode in TRUNK_MODES:
            if raw.get("native_vlan") is not None:
                nv[NATIVE_VLAN] = raw["native_vlan"]
            if raw.get("allowed_vlans") is not None:
                nv[ALLOWED_VLANS] = raw["allowed_vlans"]
        nv.setdefault(NATIVE_VLAN, PO_NATIVE_NEUTRAL)
        nv.setdefault(ALLOWED_VLANS, "")
        nv["PO_ID"] = have_nv.get("PO_ID", ifname)
        nv["MEMBER_INTERFACES"] = members_text
        nv["PVLAN_MODE"] = mode
        if raw.get("cmds") is not None:
            nv["CONF"] = freeform_merged(nv.get("CONF", ""), raw["cmds"])
        apply_native_companions(nv, raw, PO_NATIVE_COMPANIONS)
    else:
        nv = po_host_nvpairs(raw, have_nv.get("PO_ID", ifname), members=members_text)
        if "PTP" in have_nv and str(have_nv["PTP"]).strip().lower() in ("true", "false"):
            nv["PTP"] = have_nv["PTP"]
    reg_values, reg_blocked = registry_companions(state, PO_HOST_POLICY, raw, have_nv, ndfc_version, patch_version)
    nv.update(reg_values)
    out["blocked"] += reg_blocked + companion_state_problems(nv, raw, have_nv)
    if out["blocked"]:
        return out
    inactive = MAPPING_LIST if active == ASSOCIATION_LIST else ASSOCIATION_LIST
    nv[active] = pairs_to_wire(active, desired_pairs) if desired_pairs else ""
    nv[inactive] = ""
    # Keep HAVE's exact representation where the value is the same: no spurious change, no type flip.
    changed = {}
    for key in sorted(nv):
        if key in have_nv:
            try:
                same = _po_same(key, have_nv[key], nv[key])
            except PvlanError as exc:
                out["blocked"].append(str(exc))
                continue
            if same:
                nv[key] = have_nv[key]
            else:
                changed[key] = nv[key]
        elif not _po_same(key, _PO_ABSENT_DEFAULT.get(key, ""), nv[key]):
            changed[key] = nv[key]
    if out["blocked"]:
        return out
    if not changed:
        out.update(nv=copy_nv(have_nv), members=members_text)
        return out
    if mode == MODE_TRUNK_SECONDARY:
        out["new_secondaries"] = sorted(set(desired_pairs) - set(current))
    out.update(nv=nv, update=True, changed=changed, members=members_text)
    return out


def copy_nv(nv):
    return json.loads(json.dumps(nv))


def po_inherited_lines(po_nv):
    """The CONF of the 'Inherited Commands' int_eth child policy the host template creates on EVERY member
    (HOST:507-526,555-560 [SRC]): the resolved MTU when not the switch default, the speed when not Auto (HOST:517-518, RC1), the duplex
    when not auto (HOST:522-523, no device-capability helper), then the PVLAN native/allowed/list lines. The `no negotiate auto`
    the template adds by device capability (HOST:519-521) is adopted from the controller (adopt_capability_lines), never predicted. The
    freeform part (findInheritedCommandsInPOFF) is empty: a freeform line it would copy is refused (po_freeform_errors)."""
    lines = []
    if _flag(po_nv, "MTU", "jumbo") == "jumbo":
        lines.append("mtu 9216")
    if speed_cli(po_nv):
        lines.append("speed %s" % speed_cli(po_nv))
    duplex = _text(po_nv, "PORT_DUPLEX_MODE")
    if duplex not in ("", "auto"):
        lines.append("duplex %s" % duplex)
    mode = po_nv.get("PVLAN_MODE")
    native = _text(po_nv, NATIVE_VLAN)
    if mode in TRUNK_MODES and native and native != "1":
        lines.append("switchport private-vlan trunk native vlan %s" % native)
    allowed = _text(po_nv, ALLOWED_VLANS)
    if mode in TRUNK_MODES and allowed:
        lines.append("switchport private-vlan trunk allowed vlan %s" % allowed)
    return lines


def po_member_nvpairs(po_nv, current_nv, current_is_member=False):
    """nvPairs the host template hands to the member (HOST:536-553): DESC and ADMIN_STATE are INHERITED from the
    member's current policy (HOST:388-408, 530-533); CONF too, but only when that policy is already the PVLAN member
    (HOST:396-400), else "". The rest comes from the parent. `__PARENT` (never sent: the module never writes a member)
    carries the parent nvPairs the member's rendered CLI depends on (inherited lines and list pairs)."""
    return {
        "PO_ID": po_nv["PO_ID"], "PC_MODE": po_nv["PC_MODE"], "PVLAN_MODE": po_nv["PVLAN_MODE"],
        "CDP_ENABLE": po_nv["CDP_ENABLE"], "lldpTransmit": po_nv["lldpTransmit"],
        "lldpReceive": po_nv["lldpReceive"], "LACP_PORT_PRIO": po_nv["LACP_PORT_PRIO"],
        "LACP_RATE": po_nv["LACP_RATE"],
        "DESC": po_nv["DESC"] if str(po_nv.get("COPY_DESC", "false")).lower() == "true" else ((current_nv or {}).get("DESC") or ""),
        "CONF": ((current_nv or {}).get("CONF") or "") if current_is_member else "",
        "ADMIN_STATE": str((current_nv or {}).get("ADMIN_STATE", "true")).strip().lower(),
        "__PARENT": copy_nv(po_nv),
    }


# The state a member must reach when ITS PVLAN port-channel is deleted: the default int_trunk_host
# (`switchport mode trunk / allowed vlan none / edge trunk / mtu 9216`) and SHUTDOWN. The controller does NOT release it
# that way by itself -- MEASURED (NDFC 12.6.0.267): after the mark-delete the member became a new int_trunk_host with
# ADMIN_STATE "true" although HOST_INTF_ADMIN_STATE is "false" and the member was down. The module therefore sets
# ADMIN_STATE "false" explicitly before any deploy (po_released_member_payload); the pre-deploy gate still requires the
# controller's expected member configuration to be exactly this model.
PO_RELEASED_MEMBER_NV = {
    "MTU": "jumbo", "SPEED": "Auto", "BPDUGUARD_ENABLED": "no", "PORTTYPE_FAST_ENABLED": "true",
    "ALLOWED_VLANS": "none", "NATIVE_VLAN": "", "ADMIN_STATE": "false", "DESC": "", "CONF": "",
}

# Measured (NDFC 12.6.0.267): the controller does not always release the member with the template
# defaults above. After the mark-delete of port-channel501, whose (never deployed) intent held MTU "default", Ethernet1/8 came back as a
# new int_trunk_host with MTU "default" (55 nvPairs, ADMIN_STATE "true"); the earlier measurement had a port-channel at MTU jumbo. So, for a
# regular port-channel, the release is judged on two separate questions:
#   * SAFETY of the released member (PO_RELEASE_SAFETY_NV, enforced): a standalone port that is administratively down, carries no VLAN
#     (allowed none, no native) and no freeform. A release outside it stops the run before the deploy;
#   * RESTORATION to the template model (PO_RELEASED_MEMBER_NV): reported per key as `restoration_delta`, never enforced and never
#     rewritten -- restoring the user's baseline is a separate, explicit operation.
# The pre-deploy gate then requires the controller's expected member configuration to be the render of the FRESH released intent (after
# the admin-down modify and its readback) and the pending to take the device there; nothing else of the comparison is relaxed.
PO_RELEASE_SAFETY_NV = (("ADMIN_STATE", "false"), ("ALLOWED_VLANS", "none"), ("NATIVE_VLAN", ""), ("CONF", ""))


def released_member_model(admin="false"):
    """The template release model (PO_RELEASED_MEMBER_NV) with the administrative state the release targets. `admin` is the
    fabric's host-interface default (HOST_INTF_ADMIN_STATE, "true" or "false"), the same value the generic reset of a host interface uses
    (dcnm_intf_get_default_eth_payload); the module never infers it."""
    return dict(PO_RELEASED_MEMBER_NV, ADMIN_STATE=_admin_word(admin))


def released_routed_children(admin="false"):
    """The own children a released int_routed_host may keep once it holds the targeted administrative state: the measured
    up set (no_shut_interface) for "true", the down set (shut_interface) for "false"."""
    return PO_ROUTED_RELEASE_CHILDREN_UP if _admin_word(admin) == "true" else PO_ROUTED_RELEASE_CHILDREN_DOWN


def _admin_word(admin):
    word = str(admin).strip().lower()
    if word not in ("true", "false"):
        raise ValueError("the released administrative state must be 'true' or 'false', not %r" % (admin,))
    return word


def po_released_member_safety_problems(nv, admin="false"):
    """Why the released member's writable nvPairs are not a safe standalone port (empty = safe). Values compared after stripping
    surrounding blanks; ADMIN_STATE and ALLOWED_VLANS case-insensitively (boolean / keyword); NATIVE_VLAN and CONF must be empty.
    ADMIN_STATE must be the targeted state `admin` (the fabric's host default; "false" keeps the original contract)."""
    if not isinstance(nv, dict):
        return ["the released member carries no nvPairs"]
    problems = []
    for key, want in PO_RELEASE_SAFETY_NV:
        if key == "ADMIN_STATE":
            want = _admin_word(admin)
        if key not in nv:
            problems.append("%s is absent from the released member" % key)
            continue
        have = str(nv[key]).strip()
        if (have.lower() if key in ("ADMIN_STATE", "ALLOWED_VLANS") else have) != want:
            problems.append("%s is %r, not %r" % (key, nv[key], want))
    return problems


def po_released_member_restoration_delta(nv):
    """Per key of the template release model (PO_RELEASED_MEMBER_NV), the value the controller actually released when it differs
    (case-insensitive, blanks stripped): {key: {"released": value, "release_model": model}}. Informational only."""
    out = {}
    for key, model in sorted(PO_RELEASED_MEMBER_NV.items()):
        have = (nv or {}).get(key, "<absent>")
        if str(have).strip().lower() != str(model).strip().lower():
            out[key] = {"released": have, "release_model": model}
    return out


# Controller metadata of an interface policy read back with its nvPairs. Classified (BOOKKEEPING, also used by the
# measured update path, which sends HAVE minus these keys): never sent back, and a readback may change, add or drop them.
PO_RELEASE_METADATA = frozenset(BOOKKEEPING)


# The ONLY mark-delete answer accepted as a confirmed deletion of one PVLAN port-channel. MEASURED (NDFC
# 12.6.0.267, recorded wire log): RETURN_CODE 200, MESSAGE "OK", DATA {"message": "Interface deleted successfully",
# "value": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": <serial>, "IfName": <Port-channelN>}]}.
PO_MARKDELETE_MESSAGE = "Interface deleted successfully"


def po_markdelete_outcome_problems(resp, serial, ifname):
    """Why ONE mark-delete answer does not confirm the deletion of `ifname` on `serial` (empty = confirmed). Any other
    shape -- an HTTP error, a non-OK message, a list or empty DATA, a missing or foreign `value` item -- is an
    UNVERIFIED outcome: the deletion may or may not have been applied."""
    if not isinstance(resp, dict):
        return ["the mark-delete answer is not a response object"]
    problems = []
    if resp.get("RETURN_CODE") != 200 or resp.get("MESSAGE") != "OK":
        problems.append("the mark-delete answered %s %s" % (resp.get("RETURN_CODE"), resp.get("MESSAGE")))
    data = resp.get("DATA")
    if not isinstance(data, dict):
        return problems + ["the mark-delete answer carries no outcome object (DATA %s)" % type(data).__name__]
    if data.get("message") != PO_MARKDELETE_MESSAGE:
        problems.append("the mark-delete message is %r" % (data.get("message"),))
    value = data.get("value")
    items = value if isinstance(value, list) else []
    named = [i for i in items if isinstance(i, dict) and str(i.get("serialNumber", "")).casefold() == str(serial).casefold()
             and str(i.get("IfName", i.get("ifName", ""))).lower() == str(ifname).lower()]
    if len(items) != 1 or len(named) != 1:
        problems.append("the mark-delete outcome names %d item(s), %d for %s" % (len(items), len(named), ifname))
    return problems


# Measured: after the mark-delete of a DEPLOYED
# port-channel the controller keeps listing it until the deploy -- interface summary entry with markDeleted true,
# complianceStatus "NA" and ONE underlay policy `interface_delete` (entity and source = the port-channel); the policy list
# holds that policy with deleted true; the port-channel's own detail answers an empty list. The released member is already
# a standalone int_trunk_host (ADMIN_STATE "true") and the pending carries `no interface port-channelN`. A port-channel that
# was never deployed disappears at once. Only this measured form counts as "deleted, awaiting the deploy".
PO_DELETE_PENDING_POLICY = "interface_delete"


# Measured: the same marked-for-deletion form, but the
# `interface_delete` policy's source is the PARENT vPC (`vpc10`), not the port-channel. `parent` states who must own the marked policy:
# omitted for a regular Po (source == the port-channel, unchanged), the expected vPC name for the child of a vPC. A source naming any
# other parent -- or the port-channel itself for a vPC child -- is refused; any other template is refused as before.
def po_marked_deleted_problem(entry, ifname, parent=None):
    """None when the interface summary `entry` listing `ifname` is the measured "marked for deletion" form; else why not."""
    if not isinstance(entry, dict):
        return "the interface summary entry is not an object"
    if entry.get("markDeleted") is not True and str(entry.get("markDeleted", "")).strip().lower() != "true":
        return "it is listed and not marked for deletion"
    state, value = summary_policy(entry, ifname)
    if state != SUMMARY_KNOWN:
        return "it is marked for deletion but its policy is unreadable: %s" % (value,)
    owner = str(ifname if parent is None else parent).lower()
    if value["templateName"] != PO_DELETE_PENDING_POLICY or value["source"].lower() != owner:
        return "it is marked for deletion but holds %s (source %r), not the controller's %s owned by %r" % (
            value["templateName"], value["source"], PO_DELETE_PENDING_POLICY, owner)
    return None


def po_released_member_payload(nv, ifname, serial, fabric, admin="false"):
    """The ONE legacy interface/modify payload of the member release: the released int_trunk_host with ALL its current
    writable nvPairs (the fresh read, minus PO_RELEASE_METADATA) and only ADMIN_STATE changed to the targeted state (the
    fabric's host default; "false" keeps the original contract). Never the generic seven-key default payload; never a stale copy."""
    out = dict((k, v) for k, v in nv.items() if k not in PO_RELEASE_METADATA)
    out["ADMIN_STATE"] = _admin_word(admin)
    intf = {"interfaceType": "INTERFACE_ETHERNET", "serialNumber": serial, "ifName": ifname, "fabricName": fabric, "nvPairs": out}
    return {"policy": TRUNK_HOST_POLICY, "interfaces": [intf]}


def po_released_member_readback_problems(before, after, admin="false"):
    """Differences between the released member's writable nvPairs before the admin-down modify and its fresh readback. Only
    ADMIN_STATE may change (and must now be the targeted state `admin`); a writable key that disappears, changes value or appears is a
    problem; PO_RELEASE_METADATA is the only tolerated difference."""
    if not isinstance(after, dict):
        return ["the member readback carries no nvPairs"]
    problems = []
    admin = _admin_word(admin)
    if str(after.get("ADMIN_STATE", "")).strip().lower() != admin:
        problems.append("ADMIN_STATE reads back %r, not %r" % (after.get("ADMIN_STATE"), admin))
    keys = (set(before) | set(after)) - PO_RELEASE_METADATA - {"ADMIN_STATE"}
    for key in sorted(keys):
        if key not in after:
            problems.append("writable nvPair %s was lost" % key)
        elif key not in before:
            problems.append("writable nvPair %s appeared (%r)" % (key, after[key]))
        elif str(after[key]) != str(before[key]):
            problems.append("writable nvPair %s changed %r -> %r" % (key, before[key], after[key]))
    return problems


# NvPairs of a PREPARED access/routed member that would render configuration; each must hold its neutral value (the values
# MEASURED on prepared members). Anything else is configuration this contract does not model: refused before any write.
_PO_PREPARED_NEUTRAL = {
    PO_ACCESS_BASELINE_POLICY: (("ACCESS_VLAN", ("",)), ("QOS_POLICY", ("",)), ("QUEUING_POLICY", ("",)), ("ENABLE_NETFLOW", ("false",)),
                                ("ENABLE_PFC", ("false",)), ("ENABLE_QOS", ("false",)), ("ENABLE_STORM_CONTROL", ("false",)),
                                ("ENABLE_MONITOR", ("false",)), ("ENABLE_ORPHAN_PORT", ("false",)), ("aclFilter", ("",))),
    PO_ROUTED_BASELINE_POLICY: (("IP", ("",)), ("PREFIX", ("",)), ("IPv6", ("",)), ("IPv6_PREFIX", ("",)), ("INTF_VRF", ("", "default")),
                                ("ROUTING_TAG", ("",)), ("dhcpServers", ("",)), ("ipv4AclIn", ("",)), ("QOS_POLICY", ("",)),
                                ("QUEUING_POLICY", ("",)), ("ENABLE_NETFLOW", ("false",)), ("ENABLE_PFC", ("false",)),
                                ("ENABLE_QOS", ("false",)), ("ENABLE_PIM_SPARSE", ("false",)), ("ospf", ("false",)),
                                ("eigrpRouting", ("false",)), ("bfdEcho", ("false",)), ("dampening", ("false",)),
                                ("macsecInterfacePolicy", ("false",))),
}
PO_PREPARED_BASELINES = frozenset(_PO_PREPARED_NEUTRAL)
# The live child policies the controller keeps on a member prepared as routed, each with the member itself as source (MEASURED:
# Routed_interface 450, interface_mtu 452, shut_interface 458); they disappeared when the port-channel was created.
PO_ROUTED_SELF_CHILDREN = frozenset(("routed_interface", "interface_mtu", "shut_interface"))

# Measured: after the mark-delete of a PVLAN port-channel the
# controller released Ethernet1/8 as a NEW int_routed_host (84 nvPairs, ADMIN_STATE "true", MTU "9216") with three child policies
# whose source is the member itself -- routed_interface 450, interface_mtu 452 and no_shut_interface 452 -- and expected
# `mtu 9216 / no shutdown / no switchport`. A routed member administratively down (in the same run) expects
# `mtu 9216 / no switchport / shutdown` and runs without the `shutdown` line (L3 default), In-Sync. The released member may therefore
# be either policy; which one is the controller's choice (consistent with the module's own default by switch role, leaf -> trunk,
# other roles -> routed, but the controller's internal rule is NOT confirmed). The FRESH read is the authority; the role is only an
# expectation recorded in the diagnostics. No other template is accepted and routed is never converted to trunk.
RELEASED_MEMBER_POLICIES = (TRUNK_HOST_POLICY, PO_ROUTED_BASELINE_POLICY)
# Own children of a released routed member, by phase: before ADMIN_STATE is normalized the measured `no_shut_interface` child is admitted
# (only with the member itself as source); once the member is down, only the measured down set (PO_ROUTED_SELF_CHILDREN) -- a surviving
# `no_shut_interface` is configuration that would bring the port up and is refused.
PO_ROUTED_RELEASE_CHILDREN_UP = frozenset(("routed_interface", "interface_mtu", "no_shut_interface"))
PO_ROUTED_RELEASE_CHILDREN_DOWN = PO_ROUTED_SELF_CHILDREN


def po_routed_member_self_children(nv):
    """The own child policies a member PREPARED as int_routed_host may hold when it joins, by ITS administrative state: the measured
    down set (shut_interface) for "false", the measured up set (no_shut_interface) for "true", nothing otherwise (an unknown
    state is refused earlier by po_member_baseline_problems). The other state's child is never set aside: it would mean an intent that
    contradicts the member's own ADMIN_STATE."""
    admin = str((nv or {}).get("ADMIN_STATE", "")).strip().lower()
    if admin == "false":
        return PO_ROUTED_RELEASE_CHILDREN_DOWN
    if admin == "true":
        return PO_ROUTED_RELEASE_CHILDREN_UP
    return frozenset()


# The neutral values of every writable nvPair of the MEASURED released int_routed_host (84 keys; GF from the measured routed baseline), minus
# the keys rendered by _render_routed_released (ADMIN_STATE, MTU, SPEED, DESC, CONF) and the metadata. A released routed member is modeled
# only while every one of these holds its neutral value; any other value -- an address, VRF, routing protocol, ACL, QoS, freeform -- is
# configuration this contract does not model, and the run stops before the deploy.
_ROUTED_RELEASE_NEUTRAL = {
    "DISABLE_IP_REDIRECTS": "false", "ENABLE_NETFLOW": "false", "ENABLE_PFC": "false", "ENABLE_PIM_SPARSE": "false", "ENABLE_QOS": "false",
    "FEC": "auto", "GF": "", "INTF_VRF": "", "IP": "", "IPv6": "", "IPv6_PREFIX": "", "NETFLOW_MONITOR": "", "NETFLOW_SAMPLER": "",
    "OSPF_AREA_ID": "0.0.0.0", "OSPF_AUTH_KEY": "", "OSPF_AUTH_KEY_ID": "1", "PIM_DR_PRIORITY": "1", "PREFIX": "", "PTP": "false",
    "QOS_POLICY": "", "QUEUING_POLICY": "", "ROUTING_TAG": "", "arpTimeout": "", "bfdEcho": "false", "dampening": "false",
    "dampeningHalfLife": "", "dampeningMaxSuppress": "", "dampeningRestart": "false", "dampeningRestartPenalty": "", "dampeningReuse": "",
    "dampeningSuppress": "", "dhcpServers": "", "eigrpBfd": "false", "eigrpBfdDisable": "false", "eigrpIpv4DistributeListDirection": "out",
    "eigrpIpv4DistributeListPrefixList": "", "eigrpIpv4Passive": "false", "eigrpIpv6DistributeListDirection": "out",
    "eigrpIpv6DistributeListPrefixList": "", "eigrpIpv6Routing": "false", "eigrpNoIpv4Passive": "false", "eigrpNoIpv6Passive": "false",
    "eigrpProcessTag": "", "eigrpRouting": "false", "eigrpShutdown": "false", "ipv4AclIn": "", "ipv4Redirects": "", "ipv6LinkLocal": "",
    "ipv6NdSuppressRa": "false", "ipv6Redirects": "", "lldpReceive": "false", "lldpTransmit": "false", "macsecFallbackKeyChainName": "",
    "macsecInterfacePolicy": "false", "macsecKeyChainName": "", "macsecPolicyName": "", "ospf": "false", "ospfAuthentication": "false",
    "ospfAuthenticationKey": "", "ospfAuthenticationKeyType": "3", "ospfBfdMode": "noChange", "ospfCost": "", "ospfDeadInterval": "",
    "ospfHelloInterval": "", "ospfMtuIgnore": "false", "ospfNetworkType": "noChange", "ospfPassiveMode": "noChange", "ospfPriority": "",
    "ospfShutdown": "false", "ospfTag": "", "ospfTransmitDelay": "", "pimBfdInstance": "false", "qosStatsSuppressed": "false",
    "queuingStats": "false",
}
_ROUTED_RELEASE_RENDERED = ("ADMIN_STATE", "MTU", "SPEED", "DESC", "CONF")
# Residual fields of a port-channel / PVLAN membership that a released member must not carry (any policy).
_RELEASE_RESIDUAL_KEYS = ("PO_ID", "PVLAN_MODE", "PC_MODE", "ASSOCIATION_LIST", "MAPPING_LIST", "PRIMARY_INTF")
_RELEASE_RESIDUAL_EMPTY = ("", '{"ASSOCIATION_LIST":[]}', '{"MAPPING_LIST":[]}')


def _routed_release_unmodeled(nv):
    """Why a released int_routed_host is outside the measured neutral form (empty = modeled)."""
    if not isinstance(nv, dict):
        return ["the released member carries no nvPairs"]
    out = []
    for key, neutral in sorted(_ROUTED_RELEASE_NEUTRAL.items()):
        have = nv.get(key, neutral)
        if str(neutral if have is None else have).strip().lower() != neutral.lower():
            out.append("%s=%r (the released routed form models only %r)" % (key, have, neutral))
    known = set(_ROUTED_RELEASE_NEUTRAL) | set(_ROUTED_RELEASE_RENDERED) | set(BOOKKEEPING) | {"INTF_NAME"}
    for key in sorted(set(nv) - known):
        if str(nv[key] if nv[key] is not None else "").strip().lower() not in ("", "false"):
            out.append("%s=%r is outside the released routed form" % (key, nv[key]))
    if _text(nv, "SPEED") not in ("", "Auto"):
        out.append("SPEED=%r (only Auto is modeled)" % (nv.get("SPEED"),))
    if _text(nv, "MTU") != "9216":
        out.append("MTU=%r (only the measured 9216 is modeled for a released routed member)" % (nv.get("MTU"),))
    if _text(nv, "DESC"):
        out.append("a description is not modeled for a released routed member")
    if _text(nv, "CONF"):
        out.append("freeform CONF is not modeled for a released routed member")
    if _flag(nv, "ADMIN_STATE", "") not in ("true", "false"):
        out.append("ADMIN_STATE=%r is not a boolean" % (nv.get("ADMIN_STATE"),))
    return out


def _render_routed_released(nv):
    """int_routed_host body for the MEASURED released neutral form only (measured expected configuration): `no switchport`, `mtu 9216` and
    `shutdown` (ADMIN_STATE false) or `no shutdown` (true). Anything outside that form is unmodeled, which refuses the deploy."""
    if _routed_release_unmodeled(nv):
        return Model((), None, (), False)
    s = {"no switchport", "mtu %s" % _text(nv, "MTU"), "shutdown" if _flag(nv, "ADMIN_STATE", "") == "false" else "no shutdown"}
    return Model(s, None, (), True)


def released_member_safety_problems(policy, nv, admin="false"):
    """Why a released member (policy + writable nvPairs) is not a safe standalone port (empty = safe). int_trunk_host keeps the
    PO_RELEASE_SAFETY_NV contract unchanged; int_routed_host must be administratively down, without residual membership fields, and in the
    measured neutral routed form (no address, VRF, routing, ACL, QoS or freeform). Any other policy is refused."""
    if policy == TRUNK_HOST_POLICY:
        return po_released_member_safety_problems(nv, admin)
    if policy != PO_ROUTED_BASELINE_POLICY:
        return ["the released member holds %r, which is not a released-member policy (%s)" % (policy, ", ".join(RELEASED_MEMBER_POLICIES))]
    if not isinstance(nv, dict):
        return ["the released member carries no nvPairs"]
    problems = []
    admin = _admin_word(admin)
    if str(nv.get("ADMIN_STATE", "")).strip().lower() != admin:
        problems.append("ADMIN_STATE is %r, not %r" % (nv.get("ADMIN_STATE"), admin))
    for key in _RELEASE_RESIDUAL_KEYS:
        if str(nv.get(key, "") or "").strip() not in _RELEASE_RESIDUAL_EMPTY:
            problems.append("residual membership field %s=%r" % (key, nv.get(key)))
    for key in (ALLOWED_VLANS, NATIVE_VLAN):
        if str(nv.get(key, "") or "").strip():
            problems.append("a routed member carries %s=%r" % (key, nv.get(key)))
    problems += _routed_release_unmodeled(nv)
    return problems


def released_member_payload(policy, nv, ifname, serial, fabric, admin="false"):
    """The ONE legacy interface/modify payload of a released member: its OWN fresh policy and ALL its current writable nvPairs
    (minus PO_RELEASE_METADATA) with only ADMIN_STATE changed to the targeted state (po_released_member_payload, policy carried)."""
    if policy not in RELEASED_MEMBER_POLICIES:
        raise ValueError("not a released-member policy: %r" % (policy,))
    payload = po_released_member_payload(nv, ifname, serial, fabric, admin)
    payload["policy"] = policy
    return payload


def released_member_readback_problems(before_policy, before, after_policy, after, admin="false"):
    """po_released_member_readback_problems plus the policy itself: the readback must hold the SAME template."""
    problems = []
    if after_policy != before_policy:
        problems.append("the member readback holds %r, not the released %r" % (after_policy, before_policy))
    return problems + po_released_member_readback_problems(before, after, admin)


def released_member_role_expectation(role):
    """The release the module's own default-by-role rule predicts (leaf -> int_trunk_host, other roles -> int_routed_host), or None when
    the role is unknown. An EXPECTATION for the diagnostics only: the fresh controller read decides."""
    if not role:
        return None
    return TRUNK_HOST_POLICY if str(role).strip().lower() == "leaf" else PO_ROUTED_BASELINE_POLICY


def released_member_contract(policy, released):
    """The explicit per-leg release contract judged after the deploy: the PO_RELEASED_MEMBER_NV keys for int_trunk_host (unchanged),
    the rendered keys plus the neutral keys for int_routed_host -- with the values of THIS fresh release."""
    keys = PO_RELEASED_MEMBER_NV if policy == TRUNK_HOST_POLICY else tuple(_ROUTED_RELEASE_RENDERED) + tuple(_ROUTED_RELEASE_NEUTRAL)
    return dict((k, released[k]) for k in keys if k in released)


PO_TS_TRUNK_MEMBER_INCIDENT = (
    "a member in switchport mode trunk (%s) cannot join a trunk secondary port-channel: NX-OS rejects `channel-group N force` "
    "with 'PVLAN TRUNK SEC config present' (measured on NX-OS 10.5(5): deploy 500, partial). Known "
    "incident pending engineering; prepare the member explicitly as access (%s) or routed (%s) before the creation, the module "
    "does not convert it" % (TRUNK_HOST_POLICY, PO_ACCESS_BASELINE_POLICY, PO_ROUTED_BASELINE_POLICY))


def po_member_baseline_problems(baseline_policy, baseline_nv, mode=None):
    """Reasons an existing Ethernet policy cannot be the baseline of a PVLAN member in this
    delivery. The host template copies the member's own ADMIN_STATE into the member policy (default "true" when it reads none),
    and the member template renders `no shutdown` / `shutdown` from it.
    For pvlan_mode trunk secondary ONLY, a member explicitly PREPARED as access or routed is admitted (measured), with
    its rendering nvPairs neutral; a trunk member is refused as the known incident. The other modes keep the trunk-only contract.
    ADMIN-UP-JOIN (MEASURED, NDFC 12.6.0.267 / NX-OS 10.5(5), host mode: a regular Po with the parent down and up, and a vPC with one
    member per peer): an int_trunk_host member whose ADMIN_STATE is an explicit "true" joins and KEEPS it -- the member policy holds
    "true", the member pending is `channel-group N force mode M` / `no shutdown`, the running holds no `shutdown`. So an explicit true
    or false is admitted and each member keeps its own value; a missing, null or other value stays unknown and is refused (never
    inferred). ADMIN-UP-ALL-MODES (user decision, OFFLINE; first live evidence expected from the user's own tests): the same holds for
    promiscuous, trunk promiscuous and, on the access/routed bases PREPARED for trunk secondary, for trunk secondary -- the four
    parent templates copy ADMIN_STATE from int_trunk_host, int_access_host and int_routed_host alike (HOST:399-407, VPC HOST:594-624).
    The admitted BASE per mode is unchanged: a trunk member stays the trunk secondary incident whatever its admin state."""
    if mode == MODE_TRUNK_SECONDARY:
        if baseline_policy == TRUNK_HOST_POLICY:
            return [PO_TS_TRUNK_MEMBER_INCIDENT]
        if baseline_policy not in PO_PREPARED_BASELINES:
            return ["the member's current policy %r is not covered for trunk secondary (only a prepared %s or %s is)"
                    % (baseline_policy, PO_ACCESS_BASELINE_POLICY, PO_ROUTED_BASELINE_POLICY)]
    elif baseline_policy != TRUNK_HOST_POLICY:
        return ["the member's current policy %r is not covered (only %s is)" % (baseline_policy, TRUNK_HOST_POLICY)]
    if not isinstance(baseline_nv, dict):
        return ["the member's current policy has no readable nvPairs"]
    problems = []
    for key, neutral in _PO_PREPARED_NEUTRAL.get(baseline_policy, ()):
        if str(baseline_nv.get(key, "") if baseline_nv.get(key) is not None else "").strip() not in neutral:
            problems.append("the prepared member carries %s=%r, configuration this contract does not model" % (key, baseline_nv.get(key)))
    admin = baseline_nv.get("ADMIN_STATE")
    admin = None if admin is None else str(admin).strip().lower()
    if admin not in ("true", "false"):
        problems.append(
            "the member's administrative state is unknown (ADMIN_STATE %r); the PVLAN member template inherits it, so only an "
            "explicit true or false is modeled" % (baseline_nv.get("ADMIN_STATE"),))
    if str(baseline_nv.get("CONF", "") or "").strip():
        problems.append("the member carries freeform CONF, which the member template would drop")
    return problems


def _po_scalars_ok(nv):
    """True when `nv` holds only values the delivery models (everything else is refused). It models, from the installed
    body (HOST:476-499, POVPC 277-314): spanning-tree port type network|normal (never with port type fast true, which the template
    rejects), orphan port, duplex, `no lacp suspend-individual` and the queuing service-policy (with ` no-stats`). RC1 adds a known
    speed (SPEED_CLI) and a freeform CONF whose every line passes po_freeform_errors (a CONF stored by another tool that fails it stays
    unmodeled, so it is refused, never rewritten)."""
    mode = nv.get("PVLAN_MODE")
    trunk = mode in TRUNK_MODES
    stp = _text(nv, "spanningTreePortType")
    return (
        speed_cli(nv) is not None
        and _flag(nv, "MTU", "jumbo") in ("jumbo", "default")
        and stp in ("", "no", "network", "normal")
        and not (stp in ("network", "normal") and _flag(nv, "PORTTYPE_FAST_ENABLED", "true") == "true")
        and _flag(nv, "PORTTYPE_FAST_ENABLED", "true") in ("true", "false")
        and _flag(nv, "BPDUGUARD_ENABLED", "true") in ("true", "false", "no")
        and _flag(nv, "ENABLE_ORPHAN_PORT", "false") in ("true", "false")
        and _flag(nv, "DISABLE_LACP_SUSPEND", "false") in ("true", "false")
        and _text(nv, "PORT_DUPLEX_MODE") in ("", "auto", "full", "half")
        and bool(_NATIVE_POLICY_NAME.match(_text(nv, "QUEUING_POLICY")) or not _text(nv, "QUEUING_POLICY"))
        and _flag(nv, "queuingStats", "false") in ("true", "false")
        and not stored_freeform_errors("CONF", nv.get("CONF", ""))
        and (trunk or not _text(nv, ALLOWED_VLANS))
        and (trunk or _text(nv, NATIVE_VLAN) == PO_NATIVE_NEUTRAL)
    )


def _po_pairs(nv, mode):
    return pairs_from_wire(nv.get(active_list_key(mode), "") or "", active_list_key(mode))


def _render_po_host(nv):
    """Interface body of int_port_channel_pvlan_host.add() (HOST:416-505) for the four modes. Unmodeled values make
    the Model unmodeled, which refuses the deploy."""
    mode = nv.get("PVLAN_MODE")
    if mode not in PVLAN_MODES or not _po_scalars_ok(nv):
        return Model((), None, (), False)
    s = {"switchport", "switchport mode private-vlan %s" % mode}
    native = _text(nv, NATIVE_VLAN)
    if mode in TRUNK_MODES and native and native != "1":
        s.add("switchport private-vlan trunk native vlan %s" % native)
    allowed = _text(nv, ALLOWED_VLANS)
    if mode in TRUNK_MODES and allowed:
        s.add("switchport private-vlan trunk allowed vlan %s" % allowed)
    if _flag(nv, "MTU", "jumbo") == "jumbo":
        s.add("mtu 9216")
    if speed_cli(nv):
        s.add("speed %s" % speed_cli(nv))  # RC1 (HOST:464-466, POVPC 263-265)
    bpdu = _flag(nv, "BPDUGUARD_ENABLED", "true")
    if bpdu == "true":
        s.add("spanning-tree bpduguard enable")
    elif bpdu == "false":
        s.add("spanning-tree bpduguard disable")
    # HOST:478-481: a spanning-tree port type other than `no` takes the place of the edge-trunk line.
    stp = _text(nv, "spanningTreePortType")
    if stp in ("network", "normal"):
        s.add("spanning-tree port type %s" % stp)
    elif _flag(nv, "PORTTYPE_FAST_ENABLED", "true") == "true":
        s.add("spanning-tree port type edge trunk")
    if _text(nv, "DESC"):
        s.add("description %s" % _text(nv, "DESC"))
    if _flag(nv, "ENABLE_ORPHAN_PORT", "false") == "true":
        s.add("vpc orphan-port suspend")
    duplex = _text(nv, "PORT_DUPLEX_MODE")
    if duplex not in ("", "auto"):
        s.add("duplex %s" % duplex)
    if _flag(nv, "DISABLE_LACP_SUSPEND", "false") == "true":
        s.add("no lacp suspend-individual")
    queuing = _text(nv, "QUEUING_POLICY")
    if queuing:
        s.add("service-policy type queuing output %s%s" % (queuing, " no-stats" if _flag(nv, "queuingStats", "false") == "true" else ""))
    s.add("no shutdown" if _flag(nv, "ADMIN_STATE", "true") == "true" else "shutdown")
    # RC1: the freeform CONF closes the stanza (HOST:562-564, POVPC 323-325), one line per command after adjustIntfFreeformConfig. That
    # helper is controller code (NOT captured); for a top-level command it is taken as the identity, the form the Ethernet path renders.
    s.update(freeform_lines(nv.get("CONF", "")))
    try:
        pairs = _po_pairs(nv, mode)
    except PvlanError:
        return Model((), None, (), False)
    return Model(s, mode, pairs, True)


# The controller's view of `channel-group N force mode M` on a physical member, MEASURED in a preview (host,
# NDFC 12.6.0.267): the member pending held only
# `no spanning-tree port type edge trunk`, `channel-group 502 force mode active` and `shutdown`, while the controller's
# expected member configuration became `channel-group 502 mode active`, `mtu 9216`, `shutdown`, `switchport`,
# `switchport mode private-vlan host`, `switchport private-vlan host-association 2210 2212`. So, in the controller's model,
# the PVLAN mode and list lines arrive with `force` and the member's own trunk switchport lines go away with it.
# The measured preview was never deployed: what the SWITCH ends up with after that pending is NOT observed (NX-OS `force` semantics is
# the expectation); live acceptance must compare the device's running configuration. Only the measured preview effect
# is modeled, and only for the modes measured (other modes: temporary refusal, not a statement about device support).
PO_FORCE_MEASURED_MODES = frozenset((MODE_HOST,))
# The same effect is applied to the
# other three modes as an explicit INFERENCE, NOT a measurement: none of them has a controller preview or a switch
# observation of a member joining through `force`. It rests on (a) the measured host preview above, (b) the captured
# templates -- the parent's 'Inherited Commands' int_eth child renders on every member the same parent-owned lines in
# all four modes (mode, list pairs and, for the trunk modes, PVLAN native/allowed; HOST:428-462,507-560) -- and (c) the
# controller expected member those templates produce. The live gate still compares the controller's expected member
# with the intent and validates the rest of the pending; the first live case of each mode measures the real form.
PO_FORCE_INFERRED_MODES = frozenset((MODE_PROMISCUOUS, MODE_TRUNK_PROMISCUOUS, MODE_TRUNK_SECONDARY))
# The member lines the force carries FROM THE PARENT, besides the mode line and the list pairs (inferred for the
# trunk modes; the host form has none). Everything else on the member is KEPT from the member's current state and must
# be changed, if at all, by an explicit line of the pending.
_PO_FORCE_PARENT_LINE = re.compile(r"^switchport private-vlan trunk (native|allowed) vlan [0-9,\-]+$")


def po_member_channel_group(po_number, pc_mode):
    """The PERSISTED channel-group line of a member (what running/expected hold)."""
    return "channel-group %s" % po_number if pc_mode == "on" else "channel-group %s mode %s" % (po_number, pc_mode)


def po_member_force_command(po_number, pc_mode):
    """The channel-group COMMAND the controller pushes when a physical interface joins the port-channel."""
    return "channel-group %s force" % po_number if pc_mode == "on" else "channel-group %s force mode %s" % (po_number, pc_mode)


def po_force_basis(mode):
    """'measured' (host), 'inferred' (the other three PVLAN modes) or None (not a PVLAN mode)."""
    if mode in PO_FORCE_MEASURED_MODES:
        return "measured"
    if mode in PO_FORCE_INFERRED_MODES:
        return "inferred"
    return None


def po_force_unmeasured(mode):
    """Reason a member CREATION in `mode` is outside the modeled contract (measured or inferred), or None."""
    if po_force_basis(mode):
        return None
    return ("the member transition through 'channel-group force' is modeled only for the PVLAN modes %s; %r is not one, "
            "so the creation is refused before any write" % (", ".join(PVLAN_MODES), mode))


def _trunk_switchport_line(line):
    return line == "switchport mode trunk" or line.startswith("switchport trunk ")


def po_member_force_transition(body, pre, post, member_force):
    """(body, pre, problems) for a member JOINING its port-channel from a standalone trunk port.

    `member_force` = {"po_number", "pc_mode", "mode"} of THIS port-channel. When the pending holds exactly once the
    force command for this port-channel number and pc_mode, that line is taken out of the body and `pre` becomes the
    state the command produces (MEASURED for host, INFERRED for the other modes: see PO_FORCE_*_MODES):
      * FROM THE PARENT: the persisted channel-group line, `switchport` + the PVLAN mode line, the list pairs and, for
        the trunk modes, the PVLAN trunk native/allowed lines (_PO_FORCE_PARENT_LINE). They are read from the intended
        member model, whose only source for them is the parent (_render_po_member / po_inherited_lines);
      * FROM THE MEMBER: every other line of its current state (mtu, shutdown, description, spanning-tree, ...), minus
        the trunk switchport lines, `no switchport` (routed, measured) and any previous PVLAN line, which the force
        replaces. A member prepared as access/routed (`baseline`) may hold only its measured lines.
    The rest of the pending is then validated against that state by the unchanged validate_transition(): a member line
    that must change still needs its own pending line. Any other channel-group line stays in the body (and is refused
    there); a force command in a mode outside the model is a problem."""
    if not member_force:
        return body, pre, []
    command = po_member_force_command(member_force["po_number"], member_force["pc_mode"])
    hits = [line for line in body if line == command]
    if not hits:
        return body, pre, []
    if len(hits) > 1:
        return body, pre, ["the pending carries %r %d times" % (command, len(hits))]
    problem = po_force_unmeasured(member_force["mode"])
    if problem:
        return body, pre, [problem]
    if post.list_kind != member_force["mode"]:
        return body, pre, ["the member's intended PVLAN mode %r is not the port-channel's %r" % (post.list_kind, member_force["mode"])]
    baseline = member_force.get("baseline")
    if baseline in PO_PREPARED_BASELINES and pre.foreign:
        return body, pre, ["the prepared member holds command(s) outside its measured baseline: %s" % sorted(pre.foreign)]
    scalars = set(line for line in pre.scalars if not _trunk_switchport_line(line) and not line.startswith("switchport mode private-vlan ")
                  and not line.startswith("switchport private-vlan ") and line != "no switchport")
    if baseline == PO_ROUTED_BASELINE_POLICY:
        # Measured: a routed port is down by the L3 default without a `shutdown` line (adminStatus 2, ADMIN_STATE
        # false), so cli_model's restored `no shutdown` is not its state; the admin line must then come from the pending itself.
        scalars.discard("no shutdown")
    scalars |= {"switchport", "switchport mode private-vlan %s" % member_force["mode"],
                po_member_channel_group(member_force["po_number"], member_force["pc_mode"])}
    scalars |= set(line for line in post.scalars if _PO_FORCE_PARENT_LINE.match(line))
    forced = Model(scalars, post.list_kind, post.pairs, pre.modeled, pre.foreign)
    return [line for line in body if line != command], forced, []


def po_member_force_reassertion(body, observed, desired, reassert):
    """(body, problems) for an EXISTING member of an UPDATED port-channel. Measured (preview,
    host, NDFC 12.6.0.267): when a port-channel update renders lines on its member (copy_description, CDP, LLDP, LACP), the controller
    re-emits the member block WITH `channel-group N force mode M` for the port-channel the member already belongs to.

    `reassert` = {"po_number", "pc_mode"} of THIS port-channel (given only for a member whose current policy is already
    int_port_channel_pvlan_member). Exactly one such line is taken out of the body ONLY when all of these hold:
      * the device AND the intended member already hold the persisted `channel-group N mode M` of this port-channel (a re-assertion,
        never a membership change);
      * the device and the intended member are both administratively down (`shutdown`): re-issuing the command on an up member is not
        modeled;
      * the PVLAN mode does not change.
    NOTHING is assumed about what the re-issued command does on the switch: `observed` is returned unchanged, so every other member
    change (MTU, description, CDP, LLDP, LACP, ...) still needs its own pending line. Any other channel-group line (another number or
    mode, the persisted form) stays in the body and is refused by validate_transition(). The device effect is NOT measured."""
    if not reassert:
        return body, []
    command = po_member_force_command(reassert["po_number"], reassert["pc_mode"])
    hits = [line for line in body if line == command]
    if not hits:
        return body, []
    if len(hits) > 1:
        return body, ["the pending carries %r %d times" % (command, len(hits))]
    persisted = po_member_channel_group(reassert["po_number"], reassert["pc_mode"])
    problems = []
    if persisted not in observed.scalars:
        problems.append("the device member does not hold %r, so the pending %r would change its membership; only a re-assertion of "
                        "the existing membership is modeled" % (persisted, command))
    if persisted not in desired.scalars:
        problems.append("the intended member does not hold %r, so %r is not a re-assertion of the intended state" % (persisted, command))
    if "shutdown" not in observed.scalars or "shutdown" not in desired.scalars:
        problems.append("the member is not administratively down on the device and in the intended state; re-asserting %r on an up "
                        "member is not modeled" % command)
    if observed.list_kind != desired.list_kind:
        problems.append("the member's PVLAN mode changes (%r -> %r); a force re-assertion never carries a mode change"
                        % (observed.list_kind, desired.list_kind))
    if problems:
        return body, problems
    return [line for line in body if line != command], []


# Measured (NDFC 12.6.0.267 / NX-OS 10.5(5), regular port-channel, PVLAN host, one admin-down member): a GUI
# change of the port-channel MTU jumbo -> default produced a pending of ONLY `interface port-channel<N>` / `no mtu 9216` (no
# member block, no force); afterwards BOTH the port-channel and its member had lost `mtu 9216` from the running configuration and
# ran at operational MTU 1500, and the controller was In-Sync (read-only PRE/POST reads).
# Measured on the same platform with companions present: a GUI change of the same port-channel MTU
# default -> jumbo produced a pending of ONLY the port-channel stanza re-emitted with `mtu 9216` (operator-provided preview, no member block,
# no force); afterwards BOTH the port-channel and its member held `mtu 9216` in the running configuration and ran at operational MTU 9216,
# nothing else changed, and the controller was In-Sync (read-only PRE/POST reads).
# The mechanism (NX-OS propagating the port-channel MTU to its member) is an inference; force played no part. Only these two transitions
# between the two template values (`mtu 9216` present / absent) are modeled.
PO_MTU_INHERITED_WITHDRAWAL = "mtu 9216"
PO_MTU_INHERITED_LINE = PO_MTU_INHERITED_WITHDRAWAL


def _mtu_lines(scalars):
    return set(s for s in scalars if s.startswith("mtu "))


def po_member_mtu_inherited_state(entry, observed, desired, member_body, ctx):
    """(state, inherited) for an EXISTING member of an UPDATED regular port-channel whose MTU goes jumbo -> default or
    default -> jumbo.

    `ctx` (given by the regular-Po update gate and by the vPC leg gate for THIS leg's child Po) =
    {"parent", "parent_desired", "parent_vocabulary", "parent_body", "parent_ok",
    "po_number", "pc_mode"}. Common conditions, all required:
      * the parent's own transition validated with no problem (`parent_ok`);
      * the member's own pending block carries no MTU line (`mtu ...` / `no mtu ...`);
      * parent and member are PVLAN host on both sides (no mode change) and `shutdown` on both sides;
      * the member holds the persisted `channel-group N mode M` of THIS port-channel on the device and in the intended state.
    WITHDRAWAL: parent and member running hold `mtu 9216`; neither intended state holds an MTU line; the parent's pending carries
    `no mtu 9216` exactly once -> the member's observed `mtu 9216` is taken as withdrawn.
    ADDITION: neither running holds an MTU line; BOTH intended states hold exactly `mtu 9216` (no other MTU line); the parent's pending
    carries `mtu 9216` exactly once and no MTU withdrawal -> the member's observed state gains `mtu 9216`.
    Nothing else of the member's state is substituted: CDP, LLDP, LACP, description, admin and membership still need their own pending
    lines, and the rest of the validation is unchanged. Otherwise (other MTU values, mixed states, a mode outside the rule below, up interfaces, an
    explicit member MTU command) the observed state is returned untouched and the ordinary validation applies.

    The mode condition is "parent and member, observed and intended, all in the SAME mode of PVLAN_MODES"
    instead of host only; every other condition above is unchanged. MEASURED for host on a regular Po and on a vPC child/member per
    peer, in both directions. Promiscuous / trunk promiscuous / trunk secondary are NOT measured."""
    line = PO_MTU_INHERITED_LINE
    if not ctx or not ctx.get("parent_ok"):
        return observed, False
    if not (observed.modeled and desired.modeled):
        return observed, False
    if any(l.startswith("mtu ") or l.startswith("no mtu") for l in member_body):
        return observed, False
    persisted = po_member_channel_group(ctx["po_number"], ctx["pc_mode"])
    if persisted not in observed.scalars or persisted not in desired.scalars:
        return observed, False
    # The SAME supported PVLAN mode (exact enum) on the member's observed and intended state, and below on the parent's: no mode
    # transition is ever modeled. Host is measured (regular Po and vPC); the other three modes are HYPOTHESES until measured.
    if observed.list_kind not in PVLAN_MODES or not observed.list_kind == desired.list_kind:
        return observed, False
    if "shutdown" not in observed.scalars or "shutdown" not in desired.scalars:
        return observed, False
    member_obs_mtu, member_des_mtu = _mtu_lines(observed.scalars), _mtu_lines(desired.scalars)
    if member_obs_mtu == {line} and not member_des_mtu:
        direction = "withdraw"
    elif not member_obs_mtu and member_des_mtu == {line}:
        direction = "add"
    else:
        return observed, False
    parent_body, parent_desired = ctx.get("parent_body") or [], ctx.get("parent_desired")
    if parent_desired is None or not parent_desired.modeled:
        return observed, False
    parent_mtu_cmds = [l for l in parent_body if l.startswith("mtu ") or l.startswith("no mtu")]
    if direction == "withdraw" and (parent_mtu_cmds != ["no " + line] or _mtu_lines(parent_desired.scalars)):
        return observed, False
    if direction == "add" and (parent_mtu_cmds != [line] or _mtu_lines(parent_desired.scalars) != {line}):
        return observed, False
    prc, parent_running = interface_stanza(entry.get("runningConfig") or [], ctx["parent"])
    if prc != 1:
        return observed, False
    parent_observed = cli_model(parent_running, ctx.get("parent_vocabulary") or DEFAULT_VOCABULARY)
    if not parent_observed.modeled:
        return observed, False
    if _mtu_lines(parent_observed.scalars) != ({line} if direction == "withdraw" else set()):
        return observed, False
    if not parent_observed.list_kind == parent_desired.list_kind == observed.list_kind:
        return observed, False
    if "shutdown" not in parent_observed.scalars or "shutdown" not in parent_desired.scalars:
        return observed, False
    scalars = observed.scalars - {line} if direction == "withdraw" else observed.scalars | {line}
    return Model(scalars, observed.list_kind, observed.pairs, observed.modeled, observed.foreign), True


def po_member_force_withdrawal(body, po_number, pc_mode):
    """(body, problems) of a member LEAVING its deleted port-channel. MEASURED: the
    controller withdraws the membership with the COMMAND form, `no channel-group N force mode M`, while the device and the
    controller's model hold the persisted `channel-group N mode M`. That one line, for this port-channel number and pc_mode
    and at most once, is read as the withdrawal of the persisted line; anything else is left to the unchanged validation."""
    command = "no " + po_member_force_command(po_number, pc_mode)
    hits = [line for line in body if line == command]
    if len(hits) > 1:
        return body, ["the pending carries %r %d times" % (command, len(hits))]
    persisted = "no " + po_member_channel_group(po_number, pc_mode)
    return [persisted if line == command else line for line in body], []


def po_member_inherited_state(observed, desired, parent_observed):
    """(state, inherited) for an EXISTING member whose port-channel's own pending changes the parent-owned lines.
    Measured: after a host-association update the pending held
    ONLY the port-channel block (withdraw the old pair + the full stanza with the new one), the controller's expected member
    held the new pair, the member's running the old one and the member pending NOTHING: NX-OS inherits the port-channel's
    PVLAN configuration on the member (observed on the device at creation; after an update deploy it is the same NX-OS
    rule, NOT yet observed). So the member's device state is read with the parent-owned part -- list pairs and, for the
    trunk modes (INFERRED), PVLAN native/allowed -- replaced by the intended one; every other member line stays as observed.
    No substitution when the PVLAN mode differs (a mode change is never inherited here), nor when the member's device
    parent-owned part is not already the port-channel's own (`parent_observed`, its running stanza): a member that diverged
    from its port-channel is not assumed to follow it."""
    if not (observed.modeled and desired.modeled and parent_observed is not None and parent_observed.modeled):
        return observed, False
    if not observed.list_kind == desired.list_kind == parent_observed.list_kind:
        return observed, False
    own = set(line for line in observed.scalars if _PO_FORCE_PARENT_LINE.match(line))
    if observed.pairs != parent_observed.pairs or own != set(line for line in parent_observed.scalars if _PO_FORCE_PARENT_LINE.match(line)):
        return observed, False
    scalars = set(line for line in observed.scalars if not _PO_FORCE_PARENT_LINE.match(line))
    scalars |= set(line for line in desired.scalars if _PO_FORCE_PARENT_LINE.match(line))
    state = Model(scalars, desired.list_kind, desired.pairs, observed.modeled, observed.foreign)
    return state, not same_state(state, observed)


# SP1 (speed-inheritance diagnosis DIAG-20261012T091312Z, MEASURED on NDFC 12.6.0.267 / N9K-C9300v 10.5(5), host mode, one member,
# admin down): after a SPEED change of a PVLAN port-channel host (Po521) or of a vPC PVLAN host (vPC522, BOTH peers, each child Po and member
# on its own serial), the controller's expected member stanza gains / loses `speed 1000` while the pending holds ONLY the port-channel
# stanza (the whole stanza with `speed 1000` on apply, `no speed 1000` on withdrawal); deploying only the port-channel makes NX-OS apply /
# remove the line on the member too (running CLI and operational speed), and the preview then converges In-Sync/0. Only `speed 1000` is
# measured: another speed, `no negotiate auto`, more than one member, an up port or another platform is NOT, and stays refused.
PO_SPEED_INHERITED_LINES = frozenset(("speed 1000",))
_SPEED_COMMAND_PREFIXES = ("speed ", "no speed", "negotiate", "no negotiate")


def _speed_lines(scalars):
    return set(line for line in scalars if _SPEED_LINE.match(line))


def po_member_speed_inherited_state(entry, observed, desired, member_body, ctx):
    """(state, inherited) for an EXISTING member whose port-channel's SPEED goes Auto -> 1Gb (addition) or 1Gb -> Auto (withdrawal), SP1.

    `ctx` is the parent context of po_member_mtu_inherited_state() (the regular-Po update gate, or the vPC leg gate for THIS leg's child Po on
    the SAME serial). Every condition is required; otherwise the observed state is returned untouched and the ordinary validation applies:
      * the parent's own transition validated with no problem (`parent_ok`): its repeated baseline lines are judged by that validation;
      * the member's own pending block carries no speed / negotiate command;
      * no `no negotiate auto` anywhere in the member's or the parent's states (not measured);
      * the member holds the persisted `channel-group N mode M` of THIS port-channel on the device and in the intended state;
      * the SAME PVLAN mode on the member (observed / intended) and on the parent (observed / intended); `shutdown` on all four;
    ADDITION: the member's observed state has no speed line and its intended state exactly one measured line L; the parent's intended state
    holds exactly L, its running none, and its pending carries L exactly once and no other speed command.
    WITHDRAWAL: the member's observed state holds exactly one measured line L and its intended state none; the parent's running holds exactly
    L, its intended state none, and its pending carries `no L` exactly once and no other speed command.
    Only L is substituted in the member's observed state; any other member difference still needs its own pending and is refused otherwise.
    The post-deploy verification is unchanged: a member that does not show the inherited state is a failure, never a corrective write."""
    if not ctx or not ctx.get("parent_ok"):
        return observed, False
    if not (observed.modeled and desired.modeled):
        return observed, False
    if any(l.startswith(_SPEED_COMMAND_PREFIXES) for l in member_body):
        return observed, False
    if NEGOTIATE_CAPABILITY_LINE in observed.scalars or NEGOTIATE_CAPABILITY_LINE in desired.scalars:
        return observed, False
    persisted = po_member_channel_group(ctx["po_number"], ctx["pc_mode"])
    if persisted not in observed.scalars or persisted not in desired.scalars:
        return observed, False
    if observed.list_kind not in PVLAN_MODES or not observed.list_kind == desired.list_kind:
        return observed, False
    if "shutdown" not in observed.scalars or "shutdown" not in desired.scalars:
        return observed, False
    member_obs, member_des = _speed_lines(observed.scalars), _speed_lines(desired.scalars)
    if not member_obs and len(member_des) == 1 and member_des <= PO_SPEED_INHERITED_LINES:
        direction, line = "add", next(iter(member_des))
    elif not member_des and len(member_obs) == 1 and member_obs <= PO_SPEED_INHERITED_LINES:
        direction, line = "withdraw", next(iter(member_obs))
    else:
        return observed, False
    parent_body, parent_desired = ctx.get("parent_body") or [], ctx.get("parent_desired")
    if parent_desired is None or not parent_desired.modeled or NEGOTIATE_CAPABILITY_LINE in parent_desired.scalars:
        return observed, False
    parent_cmds = [l for l in parent_body if l.startswith(_SPEED_COMMAND_PREFIXES)]
    if direction == "add" and (parent_cmds != [line] or _speed_lines(parent_desired.scalars) != {line}):
        return observed, False
    if direction == "withdraw" and (parent_cmds != ["no " + line] or _speed_lines(parent_desired.scalars)):
        return observed, False
    prc, parent_running = interface_stanza(entry.get("runningConfig") or [], ctx["parent"])
    if prc != 1:
        return observed, False
    parent_observed = cli_model(parent_running, ctx.get("parent_vocabulary") or DEFAULT_VOCABULARY)
    if not parent_observed.modeled or NEGOTIATE_CAPABILITY_LINE in parent_observed.scalars:
        return observed, False
    if _speed_lines(parent_observed.scalars) != (set() if direction == "add" else {line}):
        return observed, False
    if not parent_observed.list_kind == parent_desired.list_kind == observed.list_kind:
        return observed, False
    if "shutdown" not in parent_observed.scalars or "shutdown" not in parent_desired.scalars:
        return observed, False
    scalars = observed.scalars | {line} if direction == "add" else observed.scalars - {line}
    return Model(scalars, observed.list_kind, observed.pairs, observed.modeled, observed.foreign), True


# DUPLEX (on a port-channel and on a vPC, MEASURED on NDFC 12.6.0.267 / N9K-C9300v 10.5(5), host mode, ONE member per Po / per leg,
# admin down, border switches): with the speed already fixed at 1000 (parent and member, unchanged), `duplex full` on the port-channel (on each vPC
# child) is accepted, the member inherits it, the controller pending holds ONLY the port-channel stanza (apply: its baseline lines, `speed 1000`
# among them, plus `duplex full`; withdrawal: `no duplex full` alone) and the member's intent and expected carry the line; the withdrawal returns
# parent and member to the baseline. NOT measured and therefore refused: `duplex half`, a speed + duplex change in one transition (refused
# before the write on an existing Po / vPC, see speed_duplex_combined_change), any other speed, an MTU change with it, an up port, other
# roles/platforms. More than one member per port-channel / leg: NOT refused by count - every member is judged on its own state (offline
# tests with several members); the live measurement covers one member per Po / leg. With speed Auto the device rejects the combination;
# see companion_state_problems.
PO_DUPLEX_INHERITED_LINES = frozenset(("duplex full",))
PO_DUPLEX_FIXED_SPEED_LINES = frozenset(("speed 1000",))
_DUPLEX_LINE = re.compile(r"^duplex [a-z]+$")
_DUPLEX_COMMAND_PREFIXES = ("duplex ", "no duplex")


def _duplex_lines(scalars):
    return set(line for line in scalars if _DUPLEX_LINE.match(line))


def po_member_duplex_inherited_state(entry, observed, desired, member_body, ctx):
    """(state, inherited) for an EXISTING member whose port-channel's DUPLEX goes auto -> full (addition) or full -> auto (withdrawal).

    `ctx` is the parent context of po_member_speed_inherited_state() (regular-Po update gate, or the vPC leg gate for THIS leg's child Po on the
    SAME serial: the parent running / pending read here is that leg's own stanza of that leg's own preview). Every condition is required;
    otherwise the observed state is returned untouched and the ordinary validation applies (the same `parent_ok`, channel-group, PVLAN mode and
    `shutdown` conditions as the speed rule):
      * the member's own pending block carries no duplex / speed / negotiate command;
      * no `no negotiate auto` anywhere;
      * the speed is FIXED AND UNCHANGED: member and parent, observed and intended, hold exactly `speed 1000`;
      * the parent's pending carries no speed command other than that line once (the stanza's baseline re-emitted on apply) and exactly one
        duplex command: `duplex full` (addition: the member holds none, intends exactly it; parent running none, intended exactly it) or
        `no duplex full` (withdrawal: the member holds exactly it, intends none; parent running exactly it, intended none).
    Only `duplex full` is substituted in the member's observed state. The post-deploy verification is unchanged: a member that does not show
    the inherited state is a failure, never a corrective write. The rule is evaluated PER MEMBER; it adds no limit on the number of members."""
    if not ctx or not ctx.get("parent_ok"):
        return observed, False
    if not (observed.modeled and desired.modeled):
        return observed, False
    if any(l.startswith(_DUPLEX_COMMAND_PREFIXES + _SPEED_COMMAND_PREFIXES) for l in member_body):
        return observed, False
    if NEGOTIATE_CAPABILITY_LINE in observed.scalars or NEGOTIATE_CAPABILITY_LINE in desired.scalars:
        return observed, False
    persisted = po_member_channel_group(ctx["po_number"], ctx["pc_mode"])
    if persisted not in observed.scalars or persisted not in desired.scalars:
        return observed, False
    if observed.list_kind not in PVLAN_MODES or not observed.list_kind == desired.list_kind:
        return observed, False
    if "shutdown" not in observed.scalars or "shutdown" not in desired.scalars:
        return observed, False
    if _speed_lines(observed.scalars) != PO_DUPLEX_FIXED_SPEED_LINES or _speed_lines(desired.scalars) != PO_DUPLEX_FIXED_SPEED_LINES:
        return observed, False
    member_obs, member_des = _duplex_lines(observed.scalars), _duplex_lines(desired.scalars)
    if not member_obs and len(member_des) == 1 and member_des <= PO_DUPLEX_INHERITED_LINES:
        direction, line = "add", next(iter(member_des))
    elif not member_des and len(member_obs) == 1 and member_obs <= PO_DUPLEX_INHERITED_LINES:
        direction, line = "withdraw", next(iter(member_obs))
    else:
        return observed, False
    parent_body, parent_desired = ctx.get("parent_body") or [], ctx.get("parent_desired")
    if parent_desired is None or not parent_desired.modeled or NEGOTIATE_CAPABILITY_LINE in parent_desired.scalars:
        return observed, False
    if _speed_lines(parent_desired.scalars) != PO_DUPLEX_FIXED_SPEED_LINES:
        return observed, False
    parent_speed_cmds = [l for l in parent_body if l.startswith(_SPEED_COMMAND_PREFIXES)]
    if parent_speed_cmds not in ([], sorted(PO_DUPLEX_FIXED_SPEED_LINES)):
        return observed, False
    parent_cmds = [l for l in parent_body if l.startswith(_DUPLEX_COMMAND_PREFIXES)]
    if direction == "add" and (parent_cmds != [line] or _duplex_lines(parent_desired.scalars) != {line}):
        return observed, False
    if direction == "withdraw" and (parent_cmds != ["no " + line] or _duplex_lines(parent_desired.scalars)):
        return observed, False
    prc, parent_running = interface_stanza(entry.get("runningConfig") or [], ctx["parent"])
    if prc != 1:
        return observed, False
    parent_observed = cli_model(parent_running, ctx.get("parent_vocabulary") or DEFAULT_VOCABULARY)
    if not parent_observed.modeled or NEGOTIATE_CAPABILITY_LINE in parent_observed.scalars:
        return observed, False
    if _speed_lines(parent_observed.scalars) != PO_DUPLEX_FIXED_SPEED_LINES:
        return observed, False
    if _duplex_lines(parent_observed.scalars) != (set() if direction == "add" else {line}):
        return observed, False
    if not parent_observed.list_kind == parent_desired.list_kind == observed.list_kind:
        return observed, False
    if "shutdown" not in parent_observed.scalars or "shutdown" not in parent_desired.scalars:
        return observed, False
    scalars = observed.scalars | {line} if direction == "add" else observed.scalars - {line}
    return Model(scalars, observed.list_kind, observed.pairs, observed.modeled, observed.foreign), True


def member_lacp_rate_problems(member, pre_nv, post_nv, pre_is_member):
    """Precondition from the member template (MEMBER:193-195, comment on the `shutdown` branch): "Cannot set/unset lacp
    rate if port is not admin down in port-channel". A request whose resulting member LACP rate differs from the current one is
    refused before any write unless that member stays administratively down. The module never lowers the admin state itself.
    The device behaviour is NOT measured; this only keeps the template's own stated precondition."""
    before = _text(pre_nv or {}, "LACP_RATE") if pre_is_member else ""
    after = _text(post_nv or {}, "LACP_RATE")
    if (before or "normal") == (after or "normal"):
        return []
    if _flag(post_nv or {}, "ADMIN_STATE", "true") == "false":
        return []
    return ["changing lacp_rate (%s -> %s) needs member %s administratively down (template precondition); it is up, and the module "
            "never changes a member's admin state" % (before or "normal", after or "normal", member)]


def _render_po_member(nv):
    """Member interface body = int_port_channel_pvlan_member.add() (MEMBER:109-205) + the parent's 'Inherited
    Commands' int_eth child (po_inherited_lines) + the parent's list pairs, which that child also renders on the
    member (HOST:428-462 append them to pvlan_inheritedCmds) [SRC]. `ptp`/`ttag` lines depend on device capability
    and are NOT modeled: a pending that carries them is refused, never waved through."""
    m = re.match(r"^port-channel([0-9]+)$", _text(nv, "PO_ID").lower())
    mode = nv.get("PVLAN_MODE")
    parent = nv.get("__PARENT")
    if not m or mode not in PVLAN_MODES or not isinstance(parent, dict) or parent.get("PVLAN_MODE") != mode:
        return Model((), None, (), False)
    # CDP, the two LLDP booleans and the LACP port priority / rate the parent hands down are rendered by the member body
    # (MEMBER:171-186); a value outside the template's own vocabulary stays unmodeled. Freeform CONF stays refused.
    prio = _text(nv, "LACP_PORT_PRIO")
    if _text(nv, "CONF") or _flag(nv, "CDP_ENABLE", "true") not in ("true", "false") \
            or _flag(nv, "lldpTransmit", "false") not in ("true", "false") or _flag(nv, "lldpReceive", "false") not in ("true", "false") \
            or not (prio == "" or (prio.isdigit() and 1 <= int(prio) <= 65535)) \
            or _text(nv, "LACP_RATE") not in ("normal", "fast") or not _po_scalars_ok(parent):
        return Model((), None, (), False)
    pc_mode = _text(nv, "PC_MODE")
    if pc_mode not in PO_PC_MODES:
        return Model((), None, (), False)
    s = {"switchport", "switchport mode private-vlan %s" % mode}
    s.add(po_member_channel_group(m.group(1), pc_mode))
    if _text(nv, "DESC"):
        s.add("description %s" % _text(nv, "DESC"))
    if _flag(nv, "CDP_ENABLE", "true") == "false":
        s.add("no cdp enable")
    if _flag(nv, "lldpTransmit", "false") == "true":
        s.add("no lldp transmit")
    if _flag(nv, "lldpReceive", "false") == "true":
        s.add("no lldp receive")
    if prio not in ("", "32768"):
        s.add("lacp port-priority %s" % prio)
    if _text(nv, "LACP_RATE") != "normal":
        s.add("lacp rate %s" % _text(nv, "LACP_RATE"))
    s.add("no shutdown" if _flag(nv, "ADMIN_STATE", "true") == "true" else "shutdown")
    s.update(po_inherited_lines(parent))
    try:
        pairs = _po_pairs(parent, mode)
    except PvlanError:
        return Model((), None, (), False)
    return Model(s, mode, pairs, True)


# ------------------------------------------------------------------ requested-set membership identity
# One explicit port per token, in the forms the existing module path already accepts and normalises for Ethernet names
# (dcnm_intf_get_if_name keeps the digits of `Ethernet1/7`, `eth1/7`, `e1/7`). Anything else -- a range such as
# `Ethernet1/5-8`, a port-channel, free text -- is NOT resolved here: the caller refuses it when it could hide a conflict.
_MEMBER_PORT = re.compile(r"^(?:ethernet|eth|e)?\s*([0-9]+/[0-9]+(?:/[0-9]+)?)$", re.IGNORECASE)


def po_member_canonical(token):
    """`ethernetX/Y` (lower case) for one explicit physical port token in any accepted spelling (`Ethernet1/8`, `eth1/8`,
    `e1/8`), else None. Comparison only: outbound payloads keep the controller's own spelling."""
    found = _MEMBER_PORT.match(str(token or "").strip())
    return "ethernet" + found.group(1) if found else None


def member_list_errors(members, key):
    """Validate explicit physical members using the module's existing identity normalization."""
    if not isinstance(members, list) or not members:
        return ["%s must be a non-empty list of physical Ethernet interfaces" % key]
    names = [po_member_canonical(m) if isinstance(m, str) else None for m in members]
    if None in names:
        return ["%s must contain physical Ethernet interface names, for example Ethernet1/9" % key]
    if len(set(names)) != len(names):
        return ["%s contains duplicate physical interfaces" % key]
    return []


def normalize_member_list(text):
    """(set of canonical lower-case port names, [tokens that could not be resolved]) from a comma/newline separated member
    list (MEMBER_INTERFACES / PEER*_MEMBER_INTERFACES wire text). Pure: no read, no transport."""
    names, unresolved = set(), []
    for raw in re.split(r"[\n,]", "" if text is None else str(text)):
        port = raw.strip()
        if not port:
            continue
        found = _MEMBER_PORT.match(port)
        if found:
            names.add("ethernet" + found.group(1))
        else:
            unresolved.append(port)
    return names, unresolved


# ================================================================== vPC PVLAN host (int_vpc_pvlan_host)
# Everything below is pure (no read, no transport) and ADDITIVE: no Ethernet or port-channel table, function
# or decision above changes. Contract sources, labelled so a fixture is never mistaken for a measurement:
#   [SRC]  the installed templates (int_vpc_pvlan_host / int_vpc_pvlan_po / int_port_channel_pvlan_member;
#          provenance limited: installed templates captured, NOT a confirmed factory SMU). HOST n / POVPC n cite their bodies.
#   [INF]  inferred from those bodies (for example that the child policies are written when the parent intent is saved).
#   [UNK]  not known until the first live case: the summary/policy-list shape of the vPC itself, the 207/deploy bodies of
#          a vPC, the release of the members after a vPC delete.
VPC_HOST_POLICY = "int_vpc_pvlan_host"
VPC_PO_POLICY = "int_vpc_pvlan_po"
VPC_NAME = re.compile(r"^vpc([1-9][0-9]{0,3})$", re.IGNORECASE)
# NATIVE_EXTEND + the declarative LACP rows: shared (not per-peer) companions of int_vpc_pvlan_host, with the
# public key the regular vPC spec already uses. The parent hands BPDU/port-type/MTU/duplex/LACP-suspend/vPC-convergence/PFC/queuing
# to BOTH int_vpc_pvlan_po children (HOST 630-688) and CDP/LACP priority/rate/COPY_DESC to BOTH members (HOST 727-860).
VPC_NATIVE_COMPANIONS = (
    ("bpdu_guard", "BPDUGUARD_ENABLED", "bpdu"),
    ("port_type_fast", "PORTTYPE_FAST_ENABLED", "bool"),
    ("mtu", "MTU", "mtu"),
    ("copy_description", "COPY_DESC", "bool"),
    ("enable_cdp", "CDP_ENABLE", "bool"),
    ("duplex", "PORT_DUPLEX_MODE", "duplex"),
    ("enable_pfc", "ENABLE_PFC", "bool"),
    ("queuing_policy", "QUEUING_POLICY", "policy"),
    ("disable_lacp_suspend_individual", "DISABLE_LACP_SUSPEND", "bool"),
    ("enable_lacp_vpc_convergence", "ENABLE_LACP_VPC_CONV", "bool"),
    ("lacp_port_priority", "LACP_PORT_PRIO", "lacp_prio"),
    ("lacp_rate", "LACP_RATE", "lacp_rate"),
    # RC1: SPEED, shared by both peers (HOST 472-499 support check on each peer's port-channel, 640/670 handed to each child, 702-706 /
    # 792-796 inherited by every member; POVPC 258-269 render).
    ("speed", "SPEED", "speed"),
    # Ingress QoS, the regular vPC public keys (enable_qos bool, qos_policy one policy-map name). Handed to both children by the
    # CORRECTED parent (qosPolicy/queuingPolicy locals, the reference int_vpc_trunk_host and every reference set) and
    # rendered by the corrected child as `service-policy type qos input <policy>[ no-stats]`. The revision INSTALLED on the test ND does
    # neither (QVPC analysis): the gate then refuses, it never models the defect as success.
    ("enable_qos", "ENABLE_QOS", "bool"),
    ("qos_policy", "QOS_POLICY", "policy"),
)
# Registry companions of the vPC parent (lldp x2, spanning_tree_port_type, disable_queuing_stats, acl_filter).
VPC_REGISTRY_KEYS = frozenset(registered_profile_keys(VPC_HOST_POLICY))
VPC_PROFILE_KEYS = frozenset((
    "mode", "pvlan_mode", "pvlan_association", "peer1_members", "peer2_members", "peer1_pcid", "peer2_pcid", "pc_mode",
    "peer1_description", "peer2_description", "admin_state",
    # The other three submodes of the same parent template (HOST 192-229 [SRC]): the mapping list of the promiscuous
    # modes and, for the trunk modes only (IsShow PVLAN_MODE!=promiscuous && !=host), the PER-PEER PVLAN native/allowed VLANs.
    "pvlan_mapping", "peer1_allowed_vlans", "peer2_allowed_vlans", "peer1_native_vlan", "peer2_native_vlan",
    # RC1: per-peer freeform (PEERn_PO_CONF -> CONF of that peer's child), the regular vPC's public keys.
    "peer1_cmds", "peer2_cmds",
) + tuple(c[0] for c in VPC_NATIVE_COMPANIONS)) | VPC_REGISTRY_KEYS
# Public per-peer fields -> the parent nvPair suffix they set on the controller's n-th serial.
VPC_PEER_TRUNK_FIELDS = (("native_vlan", "PVLAN_NATIVE_VLAN"), ("allowed_vlans", "PVLAN_ALLOWED_VLANS"))
# Top-level declarations of the parent (HOST variables, 42 declared = 39 here + SERIAL_NUMBER, INTF_NAME, PTP which the
# controller owns), in wire form. Sent EXPLICITLY on create and on every update so that no omission can mean "keep" in one
# route and "reset" in the other.
VPC_TEMPLATE_DEFAULTS = (
    ("PC_MODE", "active"),
    ("BPDUGUARD_ENABLED", "true"),
    ("PORTTYPE_FAST_ENABLED", "true"),
    ("spanningTreePortType", "no"),
    ("MTU", "jumbo"),
    ("SPEED", "Auto"),
    ("COPY_DESC", "false"),
    ("CDP_ENABLE", "true"),
    ("lldpTransmit", "false"),
    ("lldpReceive", "false"),
    ("PORT_DUPLEX_MODE", "auto"),
    ("DISABLE_LACP_SUSPEND", "false"),
    ("ENABLE_LACP_VPC_CONV", "false"),
    ("LACP_PORT_PRIO", 32768),  # declared `integer`; the measured vPC trunk payload also sends an integer
    ("LACP_RATE", "normal"),
    ("ADMIN_STATE", "true"),
    ("ENABLE_PFC", "false"),
    ("ENABLE_QOS", "false"),
    ("QOS_POLICY", ""),
    ("qosStatsSuppressed", "false"),
    ("QUEUING_POLICY", ""),
    ("queuingStats", "false"),
    ("aclFilter", ""),
    ("ENABLE_MIRROR_CONFIG", "false"),  # declared and unused by the body (HOST variables)
)
_VPC_PEER_KEYS = ("PEER1_PCID", "PEER2_PCID", "PEER1_MEMBER_INTERFACES", "PEER2_MEMBER_INTERFACES", "PEER1_PO_DESC",
                  "PEER2_PO_DESC", "PEER1_PO_CONF", "PEER2_PO_CONF", "PEER1_PVLAN_ALLOWED_VLANS", "PEER2_PVLAN_ALLOWED_VLANS",
                  "PEER1_PVLAN_NATIVE_VLAN", "PEER2_PVLAN_NATIVE_VLAN")
VPC_KNOWN_HAVE_NVPAIRS = frozenset(
    tuple(k for k, _d in VPC_TEMPLATE_DEFAULTS) + _VPC_PEER_KEYS
    + ("SERIAL_NUMBER", "INTF_NAME", "PTP", "PVLAN_MODE", MAPPING_LIST, ASSOCIATION_LIST, "PRIMARY_INTF") + BOOKKEEPING)
# Measured: a created vPC parent carries `createVpc` = "true" in its nvPairs. It is NOT a field of the installed
# int_vpc_pvlan_host template (no variable, no use in its body; VPC-TEMPLATE-READ) and the collection's own dcnm_interface schema lists it as
# an optional controller string; the vPC access host captures show it too ("false"). It is classified as READ-ONLY controller metadata:
# only the exact boolean spellings are accepted (any other value stays unclassifiable and blocks), it is never written by the module on
# create, and an update echoes the controller's own value unchanged (never dropped, never overridden). Nothing else is waived.
VPC_CONTROLLER_METADATA = {"createVpc": ("true", "false")}
_VPC_BOOL_KEYS = _PO_BOOL_KEYS + ("ENABLE_LACP_VPC_CONV", "ENABLE_PFC", "ENABLE_QOS", "qosStatsSuppressed", "ENABLE_MIRROR_CONFIG")
_VPC_ABSENT_DEFAULT = dict(list(VPC_TEMPLATE_DEFAULTS) + [
    ("PEER1_PO_DESC", ""), ("PEER2_PO_DESC", ""), ("PEER1_PO_CONF", ""), ("PEER2_PO_CONF", ""),
    ("PEER1_PVLAN_ALLOWED_VLANS", ""), ("PEER2_PVLAN_ALLOWED_VLANS", ""), ("PEER1_PVLAN_NATIVE_VLAN", ""),
    ("PEER2_PVLAN_NATIVE_VLAN", ""), (MAPPING_LIST, ""), (ASSOCIATION_LIST, "")])

# The child Po body (POVPC 59-170) is the regular Po host body plus `vpc <id>`; its tables are separate from the Po ones.
# The child body also renders `lacp vpc-convergence` (POVPC 292-293) and `ip port access-group <acl> in` (POVPC 318-321).
_VPC_GRAMMAR[VPC_PO_POLICY] = _PO_GRAMMAR[PO_HOST_POLICY] + (r"vpc [0-9]+", r"lacp vpc-convergence", r"ip port access-group \S+ in",
                                                             # The corrected child's qos line with its ' no-stats' suffix
                                                             r"service-policy type qos input \S+ no-stats")
_VPC_NAMESPACES[VPC_PO_POLICY] = _PO_NAMESPACES[PO_HOST_POLICY] + ("vpc", "ip port access-group")
VPC_VOCABULARY_POLICIES = tuple(sorted(_VPC_GRAMMAR))


def vpc_id(ifname):
    """Digits of a vPC interface name ('vPC10' -> '10'), or None."""
    m = VPC_NAME.match(str(ifname or "").strip())
    return m.group(1) if m else None


def vpc_not_implemented(profile, ifname):
    """Reasons a vPC PVLAN request is outside the delivery (empty = in scope). Decided from the RAW profile, before any default or
    coercion and before any read. The four PVLAN submodes of int_vpc_pvlan_host; per submode only the fields its template
    shows (association: host/trunk secondary; mapping: promiscuous/trunk promiscuous; per-peer native/allowed: the trunk modes) and the
    template's own list limits. Still deferred: empty member lists, a PCID CHANGE of an existing vPC, an empty list, a mode change.
    RC1: per-peer freeform (`peerN_cmds`) under po_freeform_errors and a non-Auto speed."""
    if not isinstance(profile, dict):
        return ["profile must be a dictionary"]
    reasons = []
    unknown = sorted(k for k in profile if k not in VPC_PROFILE_KEYS and k not in INJECTED_KEYS)
    if unknown:
        reasons.append("field(s) not implemented for a vPC in mode 'pvlan': %s" % ", ".join(unknown))
    for key in sorted(k for k in profile if k in VPC_PROFILE_KEYS):
        if profile[key] is None:
            reasons.append("%s must not be null" % key)
    vid = vpc_id(ifname)
    if vid is None:
        reasons.append("the vPC name must be vPC<1-9999>, for example vPC10")
    mode = profile.get("pvlan_mode")
    if "pvlan_mode" not in profile:
        reasons.append("pvlan_mode is required for mode 'pvlan'")
        return reasons
    if mode not in PVLAN_MODES:
        reasons.append("pvlan_mode must be one of: %s" % ", ".join(PVLAN_MODES))
        return reasons
    for peer in ("peer1", "peer2"):
        key = peer + "_members"
        if key in profile and profile[key] is not None:
            members = profile[key]
            reasons += member_list_errors(members, key)
        pcid = peer + "_pcid"
        # Same contract as the regular vPC: optional integer 1-4096 per peer, independent of the vPC id and of the other peer; omitted
        # means the vPC id on a creation and the existing value on an update (vpc_pair_view / reconcile_vpc).
        if pcid in profile and profile.get(pcid) is not None:
            if isinstance(profile[pcid], bool) or not isinstance(profile[pcid], int) or not 1 <= profile[pcid] <= 4096:
                reasons.append("%s must be an integer from 1 to 4096 (the port-channel number of that peer)" % pcid)
        desc = peer + "_description"
        if desc in profile and profile[desc] is not None:
            value = profile[desc]
            # A1-CLEAR: an explicit "" is the request to clear THIS peer's description (merged; omission still keeps it). Any other value
            # stays a single-line string (no LF, no CR) of at most 254 characters.
            if not isinstance(value, str) or len(value) > 254 or "\n" in value or "\r" in value:
                reasons.append("%s must be a single-line string of at most 254 characters (\"\" clears that peer's description)" % desc)
        reasons += _vpc_peer_trunk_errors(profile, peer, mode)
        if profile.get(peer + "_cmds") is not None:
            reasons += po_freeform_errors(peer + "_cmds", profile[peer + "_cmds"])
    for field, allowed_modes in (("pvlan_association", ASSOCIATION_MODES), ("pvlan_mapping", MAPPING_MODES)):
        value = profile.get(field)
        if value is None:
            continue
        if mode not in allowed_modes:
            reasons.append("%s is not valid for pvlan_mode '%s'" % (field, mode))
            continue
        if not isinstance(value, list) or not value:
            reasons.append("an empty %s is not implemented for a vPC" % field)
            continue
        try:
            pairs = requested_pairs(field, value)
            reasons += limit_errors(mode, pairs)
        except PvlanError as exc:
            reasons.append(str(exc))
    pc_mode = profile.get("pc_mode")
    if pc_mode is not None and pc_mode not in PO_PC_MODES:
        reasons.append("pc_mode must be one of: %s" % ", ".join(PO_PC_MODES))
    if "admin_state" in profile and profile["admin_state"] is not None and not isinstance(profile["admin_state"], bool):
        reasons.append("admin_state must be a boolean")
    reasons += native_companion_errors(profile, VPC_NATIVE_COMPANIONS)
    reasons += registry_companion_errors(VPC_HOST_POLICY, profile)
    return reasons


def _vpc_peer_trunk_errors(profile, peer, mode):
    """Errors of the per-peer PVLAN native/allowed fields of one peer (raw profile). Same value rules as the regular
    port-channel (po_not_implemented) and the template's own refusal of 'all' (HOST 318-320 [SRC]); valid only for the trunk modes."""
    reasons = []
    for suffix, _nv in VPC_PEER_TRUNK_FIELDS:
        key = "%s_%s" % (peer, suffix)
        value = profile.get(key)
        if value is None:
            continue
        if mode not in TRUNK_MODES:
            reasons.append("%s is valid only for pvlan_mode trunk promiscuous or trunk secondary" % key)
            continue
        if not isinstance(value, str):
            reasons.append("%s must be a string" % key)
        elif suffix == "native_vlan":
            if value != "" and (not re.match(r"^[1-9][0-9]{0,3}$", value) or not 1 <= int(value) <= 4094):
                reasons.append("%s must be '' or one VLAN ID 1-4094" % key)
        elif value.strip().lower() == "all":
            reasons.append("%s 'all' is refused by int_vpc_pvlan_host; give explicit ranges" % key)
        elif value not in ("", "none"):
            try:
                vlan_set(value, key)
            except PvlanError as exc:
                reasons.append(str(exc))
    return reasons


def vpc_pair_view(raw, combined, playbook_serials, ifname=None):
    """The two legs of a vPC in the controller's pair order, each bound to ITS serial. `peer1_*` of the playbook belong to
    `switch[0]` (the module's existing vPC contract), which may be the controller's second serial. Raises PvlanError when the
    playbook switches are not exactly the two serials of the pair. Returns [{serial, index, playbook_peer, member, pcid, desc}]."""
    parts = str(combined or "").split("~")
    if len(parts) != 2 or not all(parts):
        raise PvlanError("the vPC pair identity %r is not <serial1>~<serial2>" % (combined,))
    serials = list(playbook_serials or [])
    if len(serials) != 2 or sorted(serials) != sorted(parts):
        raise PvlanError("the playbook switches %s are not the two switches of the vPC pair %s" % (serials, combined))
    legs = []
    for index, serial in enumerate(parts):
        peer = serials.index(serial) + 1
        members = raw.get("peer%d_members" % peer)
        legs.append({
            "serial": serial, "index": index, "playbook_peer": peer,
            "member": ",".join(m.strip() for m in members) if isinstance(members, list) and members else None,
            # The port-channel number of THIS serial: the operator's value, else the vPC id (the regular vPC default). `pcid_given`
            # tells an update whether to keep the existing one (omitted) or to refuse a change (explicit).
            "pcid": raw.get("peer%d_pcid" % peer) if raw.get("peer%d_pcid" % peer) is not None else vpc_id(ifname) if ifname else None,
            "pcid_given": raw.get("peer%d_pcid" % peer) is not None,
            "desc": raw.get("peer%d_description" % peer),
            # Per-peer PVLAN trunk native/allowed of THIS serial (None = omitted).
            "native": raw.get("peer%d_native_vlan" % peer),
            "allowed": raw.get("peer%d_allowed_vlans" % peer),
            # RC1: per-peer freeform of THIS serial (None = omitted).
            "cmds": raw.get("peer%d_cmds" % peer),
        })
    return legs


def vpc_po_name(pcid):
    """The per-peer port-channel the parent template names (HOST 267-271): lower-case, from the PCID."""
    return "port-channel%s" % pcid


def vpc_host_nvpairs(raw, ifname, legs, members=None):
    """The EXPLICIT payload of int_vpc_pvlan_host for a creation or a `replaced` update: the template's declarations and the
    operator's input, in the declared (or measured vPC-trunk) types; nothing copied from another policy. `raw` has passed
    vpc_not_implemented(); `legs` is vpc_pair_view(). PEERn_* belong to the controller's n-th serial."""
    nv = {}
    for key, default in VPC_TEMPLATE_DEFAULTS:
        nv[key] = default
    if raw.get("pc_mode") is not None:
        nv["PC_MODE"] = raw["pc_mode"]
    if raw.get("admin_state") is not None:
        nv["ADMIN_STATE"] = "true" if raw["admin_state"] else "false"
    mode = raw.get("pvlan_mode", MODE_HOST)
    trunk = mode in TRUNK_MODES
    nv["PVLAN_MODE"] = mode
    for leg in legs:
        n = leg["index"] + 1
        member = (members[leg["index"]] if members is not None else leg["member"]) or ""
        nv["PEER%d_PCID" % n] = str(leg["pcid"])  # declared integer; the measured vPC trunk payload sends it as a string
        nv["PEER%d_MEMBER_INTERFACES" % n] = member
        nv["PEER%d_PO_DESC" % n] = leg["desc"] if leg["desc"] is not None else ""
        nv["PEER%d_PO_CONF" % n] = "\n".join(freeform_request(leg["cmds"])) if leg.get("cmds") is not None else ""
        # Per-peer native/allowed only in the trunk modes; a native VLAN is sent as a string of digits (the form measured
        # accepted for the integer-declared regular Po field, TP1/TS1 live); neutral '' otherwise.
        nv["PEER%d_PVLAN_ALLOWED_VLANS" % n] = (leg.get("allowed") or "") if trunk else ""
        nv["PEER%d_PVLAN_NATIVE_VLAN" % n] = (leg.get("native") or PO_NATIVE_NEUTRAL) if trunk else PO_NATIVE_NEUTRAL
    field = _po_list_field(mode)
    active = active_list_key(mode)
    pairs = requested_pairs(field, raw[field]) if raw.get(field) is not None else []
    nv[MAPPING_LIST] = pairs_to_wire(MAPPING_LIST, pairs) if active == MAPPING_LIST and pairs else ""
    nv[ASSOCIATION_LIST] = pairs_to_wire(ASSOCIATION_LIST, pairs) if active == ASSOCIATION_LIST and pairs else ""
    # Explicit native companions replace their template declaration (shared by both peers); registry companions are
    # added by the caller (reconcile_vpc / the payload builder).
    apply_native_companions(nv, raw, VPC_NATIVE_COMPANIONS)
    return vpc_qos_normalize(nv, raw, full=True)


def _vpc_norm(key, value):
    if value is None:
        return None
    text = str(value).strip()
    if key in _VPC_BOOL_KEYS or key == "PORT_DUPLEX_MODE":
        return text.lower()
    if key in ("PEER1_MEMBER_INTERFACES", "PEER2_MEMBER_INTERFACES"):
        # The same port in any accepted spelling (`Ethernet1/8`, `e1/8`) compares equal, as for the regular port-channel.
        return _po_norm("MEMBER_INTERFACES", value)
    if key in ("PEER1_PCID", "PEER2_PCID", "LACP_PORT_PRIO"):
        return text
    return text


def _vpc_same(key, have_value, want_value):
    if key in ("PEER1_PO_CONF", "PEER2_PO_CONF", "CONF"):
        return _freeform_same(have_value, want_value)
    if key in (MAPPING_LIST, ASSOCIATION_LIST, NATIVE_VLAN, ALLOWED_VLANS):
        return _po_same(key, have_value, want_value)
    if key in ("PEER1_PVLAN_NATIVE_VLAN", "PEER2_PVLAN_NATIVE_VLAN"):
        return native_equal(have_value or "", want_value or "")
    if key in ("PEER1_PVLAN_ALLOWED_VLANS", "PEER2_PVLAN_ALLOWED_VLANS"):
        return allowed_equal(have_value or "", want_value or "")
    return _vpc_norm(key, have_value) == _vpc_norm(key, want_value)


def _vpc_ask_legs(changed):
    """Legs (controller order, 0/1) a change of these nvPairs reaches. A per-peer description reaches only that peer; every
    shared field (association, admin state, PC mode) reaches both."""
    legs = set()
    for key in changed:
        if key in ("PEER1_PO_DESC", "PEER1_PVLAN_NATIVE_VLAN", "PEER1_PVLAN_ALLOWED_VLANS", "PEER1_MEMBER_INTERFACES", "PEER1_PO_CONF"):
            legs.add(0)
        elif key in ("PEER2_PO_DESC", "PEER2_PVLAN_NATIVE_VLAN", "PEER2_PVLAN_ALLOWED_VLANS", "PEER2_MEMBER_INTERFACES", "PEER2_PO_CONF"):
            legs.add(1)
        else:
            legs.update((0, 1))
    return sorted(legs)


def reconcile_vpc(state, raw, ifname, legs, have_policy, have_nv, ndfc_version=None, patch_version=None):
    """Decision for ONE vPC PVLAN WANT against its HAVE: {nv, update, creates, changed, blocked, members, ask_legs, new_secondaries}.

    Native companions (VPC_NATIVE_COMPANIONS, shared by both peers) follow the merged/replaced rule of the other shared
    scalars; registry companions follow registry_companions() (ndfc_version/patch_version are used for them only).

      * HAVE absent -> creation with the explicit payload (one or more members per peer and the submode's list are required);
      * HAVE is this policy, the SAME submode, explicit physical members per peer, PCID = vPC id, a stored freeform that passes
        po_freeform_errors (RC1) -> update. `merged` keeps
        every omitted field from HAVE (the active list is the union); `replaced` states the complete model (members and PCIDs from
        HAVE). An equal request is a no-op;
      * another policy, a submode/member/PCID change, stored CONF, unclassifiable HAVE fields, the promiscuous partial removal (the
        protection kept from the measured Ethernet defect), or a change that reaches ONE peer only (the unilateral update of a vPC is
        NOT implemented: its modify behaviour is unmeasured) -> blocked. MM-B: a change of ONE peer's MEMBERSHIP only (add/remove members
        on that peer, regular rule) is admitted; the other peer keeps its state.
    Submodes promiscuous / trunk promiscuous (MAPPING_LIST) and trunk secondary (ASSOCIATION_LIST) next to host, with the
    per-peer PVLAN native/allowed of the trunk modes. `new_secondaries` (trunk secondary) are typed by the caller before any write."""
    out = {"nv": None, "update": False, "creates": False, "changed": {}, "blocked": [], "members": None, "ask_legs": [],
           "new_secondaries": [], "added": {}, "removed": {}}
    vid = vpc_id(ifname)
    mode = raw.get("pvlan_mode", MODE_HOST)
    field = _po_list_field(mode)
    active = active_list_key(mode)
    if have_policy is None:
        if any(leg["member"] is None for leg in legs):
            out["blocked"].append("peer1_members and peer2_members are required to create a vPC: one or more existing physical members per peer")
        if not raw.get(field):
            out["blocked"].append("%s is required to create a vPC in pvlan_mode %s" % (field, mode))
        if out["blocked"]:
            return out
        nv = vpc_host_nvpairs(raw, ifname, legs)
        reg_values, reg_blocked = registry_companions(state, VPC_HOST_POLICY, raw, None, ndfc_version, patch_version)
        nv.update(reg_values)
        out["blocked"] += reg_blocked + companion_state_problems(nv, raw)
        if out["blocked"]:
            return out
        out.update(nv=nv, creates=True, changed=dict(nv), members=[nv["PEER1_MEMBER_INTERFACES"], nv["PEER2_MEMBER_INTERFACES"]],
                   ask_legs=[0, 1])
        if mode == MODE_TRUNK_SECONDARY:
            out["new_secondaries"] = sorted(pairs_from_wire(nv[ASSOCIATION_LIST], ASSOCIATION_LIST))
        return out
    if have_policy != VPC_HOST_POLICY:
        out["blocked"].append("the vPC already holds policy %s; converting it to int_vpc_pvlan_host is not implemented" % have_policy)
        return out
    if not isinstance(have_nv, dict):
        out["blocked"].append("the controller returned no nvPairs for the existing vPC")
        return out
    have_mode = have_nv.get("PVLAN_MODE")
    if have_mode not in PVLAN_MODES:
        out["blocked"].append("current PVLAN_MODE %r is not a known int_vpc_pvlan_host mode" % (have_mode,))
    elif have_mode != mode:
        out["blocked"].append("changing pvlan_mode of an existing vPC (%r -> %r) is not implemented" % (have_mode, mode))
    lost = sorted(k for k in have_nv if k not in VPC_KNOWN_HAVE_NVPAIRS and have_nv[k] not in ("", None)
                  and not (k in VPC_CONTROLLER_METADATA and str(have_nv[k]).strip().lower() in VPC_CONTROLLER_METADATA[k]))
    if lost:
        out["blocked"].append("the vPC holds nvPair(s) this module cannot classify and a full-set update could clear: %s" % ", ".join(lost))
    have_members = []
    for n in (1, 2):
        names, unresolved = normalize_member_list(have_nv.get("PEER%d_MEMBER_INTERFACES" % n))
        if unresolved or not names:
            out["blocked"].append("peer %d needs a readable, non-empty list of explicit physical members" % n)
        have_members.append(names)
        have_pcid = str(have_nv.get("PEER%d_PCID" % n, "")).strip()
        if not re.match(r"^[1-9][0-9]{0,3}$", have_pcid) or int(have_pcid) > 4096:
            out["blocked"].append("PEER%d_PCID %r is not a readable port-channel number" % (n, have_nv.get("PEER%d_PCID" % n)))
        # RC1: a stored per-peer freeform is accepted only when every command passes the same rule as a requested one; anything else
        # (a command the controller copies to the members, a structured field's command, a sub-mode block) is refused, never rewritten.
        stored = stored_freeform_errors("PEER%d_PO_CONF" % n, have_nv.get("PEER%d_PO_CONF" % n, ""))
        if stored:
            out["blocked"].append("the vPC stores freeform commands on peer %d (PEER%d_PO_CONF) outside the modeled freeform rule: %s"
                                  % (n, n, "; ".join(stored)))
    # The port-channel number of an existing vPC never changes (the regular contract): an explicit value must equal the stored one of THAT
    # controller peer; an omitted one keeps it. The legs are copied so the caller's list is untouched.
    legs = [dict(leg) for leg in legs]
    for leg in legs:
        stored = str(have_nv.get("PEER%d_PCID" % (leg["index"] + 1), "")).strip()
        if leg.get("pcid_given") and str(leg["pcid"]) != stored:
            out["blocked"].append("peer%d_pcid %s differs from the stored PEER%d_PCID %s of that peer; changing the port-channel number of an "
                                  "existing vPC is not implemented" % (leg["playbook_peer"], leg["pcid"], leg["index"] + 1, stored))
        leg["pcid"] = stored
    if out["blocked"]:
        return out
    # MM-B: per peer, the membership follows the regular rule (member_list_update): merged = union, replaced/overridden = exactly the
    # requested members of that peer; an omitted or empty peer list in replaced/overridden is refused (an empty member list is not
    # implemented). A member added or removed on one peer does not touch the other peer.
    members = [have_nv.get("PEER1_MEMBER_INTERFACES", ""), have_nv.get("PEER2_MEMBER_INTERFACES", "")]
    out["added"], out["removed"] = {}, {}
    for leg in legs:
        requested = str(leg["member"]).split(",") if leg["member"] is not None else None
        text, added, removed = member_list_update(state, members[leg["index"]], requested)
        if text is None:
            out["blocked"].append(
                "%s states the exact member list of each peer of an existing vPC: an omitted or empty peer%d_members would remove every member "
                "of that peer, and an empty member list is not implemented; list the members explicitly" % (state, leg["index"] + 1))
            continue
        members[leg["index"]] = text
        if added:
            out["added"][leg["index"]] = added
        if removed:
            out["removed"][leg["index"]] = removed
    if out["blocked"]:
        return out
    # peerN_* of the playbook are bound to the serial that owns them; the controller-order nvPairs come from the legs.
    merged = state == "merged"
    current = pairs_from_wire(have_nv.get(active, "") or "", active)
    requested = requested_pairs(field, raw[field]) if raw.get(field) is not None else None
    desired = sorted(set(current) | set(requested or [])) if merged else sorted(set(requested or []))
    out["blocked"] += limit_errors(mode, desired)
    if not desired:
        # the host text is kept byte-for-byte; the promiscuous modes name their mapping
        out["blocked"].append("an empty %s is not implemented for a vPC" % ("association" if field == "pvlan_association" else "mapping"))
    if promiscuous_partial_removal(have_mode, mode, current, desired):
        out["blocked"].append(
            "removing secondary VLAN(s) %s from a promiscuous mapping that keeps other secondaries is blocked (protection kept from the "
            "measured Ethernet defect; its behaviour on a vPC is NOT measured). Remove the whole vPC instead"
            % ", ".join("%d/%d" % p for p in sorted(set(current) - set(desired))))
    if out["blocked"]:
        return out
    if merged:
        nv = dict((k, v) for k, v in have_nv.items() if (k in VPC_KNOWN_HAVE_NVPAIRS or k in VPC_CONTROLLER_METADATA) and k not in BOOKKEEPING)
        for key, default in VPC_TEMPLATE_DEFAULTS:
            nv.setdefault(key, default)
        for key in _VPC_PEER_KEYS:
            nv.setdefault(key, _VPC_ABSENT_DEFAULT.get(key, ""))
        if raw.get("pc_mode") is not None:
            nv["PC_MODE"] = raw["pc_mode"]
        if raw.get("admin_state") is not None:
            nv["ADMIN_STATE"] = "true" if raw["admin_state"] else "false"
        for leg in legs:
            if leg["desc"] is not None:
                nv["PEER%d_PO_DESC" % (leg["index"] + 1)] = leg["desc"]
            if leg.get("cmds") is not None:
                key = "PEER%d_PO_CONF" % (leg["index"] + 1)
                nv[key] = freeform_merged(nv.get(key, ""), leg["cmds"])
            if mode in TRUNK_MODES:
                if leg.get("native") is not None:
                    nv["PEER%d_PVLAN_NATIVE_VLAN" % (leg["index"] + 1)] = leg["native"]
                if leg.get("allowed") is not None:
                    nv["PEER%d_PVLAN_ALLOWED_VLANS" % (leg["index"] + 1)] = leg["allowed"]
        nv["PVLAN_MODE"] = mode
        nv["PEER1_MEMBER_INTERFACES"], nv["PEER2_MEMBER_INTERFACES"] = members
        apply_native_companions(nv, raw, VPC_NATIVE_COMPANIONS)
        vpc_qos_normalize(nv, raw, full=False)
    else:
        nv = vpc_host_nvpairs(raw, ifname, legs, members=members)
        for key in VPC_CONTROLLER_METADATA:
            if key in have_nv and have_nv[key] not in ("", None):
                nv[key] = have_nv[key]
        if "PTP" in have_nv and str(have_nv["PTP"]).strip().lower() in ("true", "false"):
            nv["PTP"] = have_nv["PTP"]
    reg_values, reg_blocked = registry_companions(state, VPC_HOST_POLICY, raw, have_nv, ndfc_version, patch_version)
    nv.update(reg_values)
    out["blocked"] += reg_blocked + companion_state_problems(nv, raw, have_nv)
    if out["blocked"]:
        return out
    inactive = MAPPING_LIST if active == ASSOCIATION_LIST else ASSOCIATION_LIST
    nv[active] = pairs_to_wire(active, desired) if desired else ""
    nv[inactive] = ""
    changed = {}
    for key in sorted(nv):
        if key in have_nv:
            try:
                same = _vpc_same(key, have_nv[key], nv[key])
            except PvlanError as exc:
                out["blocked"].append(str(exc))
                continue
            if same:
                nv[key] = have_nv[key]
            else:
                changed[key] = nv[key]
        elif not _vpc_same(key, _VPC_ABSENT_DEFAULT.get(key, ""), nv[key]):
            changed[key] = nv[key]
    if out["blocked"]:
        return out
    if not changed:
        out.update(nv=copy_nv(have_nv), members=members)
        return out
    ask = _vpc_ask_legs(changed)
    membership_only = set(changed) <= set("PEER%d_MEMBER_INTERFACES" % (i + 1) for i in ask)
    # The description of ONE peer may change alone. PEERn_PO_DESC feeds only that peer's child port-channel (template HOST 643/673), so the
    # other peer is neither touched nor mirrored; its convergence is still judged by the per-leg gate (`expect` = converged). With COPY_DESC
    # true the parent copies that description to the MEMBERS of the peer, a path this increment does not model: refused before any write.
    description_only = len(ask) == 1 and set(changed) == set(["PEER%d_PO_DESC" % (ask[0] + 1)])
    if description_only and _vpc_norm("COPY_DESC", nv.get("COPY_DESC", "false")) == "true":
        out["blocked"].append(
            "a description change that reaches only peer %d is not implemented while copy_description is true: the controller would also copy "
            "it to the members of that peer. Set copy_description to false, or change the description of both peers" % (ask[0] + 1))
        return out
    if len(ask) == 1 and not membership_only and not description_only:
        out["blocked"].append(
            "this request changes only peer %d of the vPC (%s); an update that reaches one peer only is not implemented "
            "(its modify behaviour is not measured). Change both peers or none" % (ask[0] + 1, ", ".join(sorted(changed))))
        return out
    if mode == MODE_TRUNK_SECONDARY:
        out["new_secondaries"] = sorted(set(desired) - set(current))
    out.update(nv=nv, update=True, changed=changed, members=members, ask_legs=ask)
    return out


def vpc_leg_po_nv(parent_nv, index, vpc_name):
    """nvPairs the parent hands to the child int_vpc_pvlan_po of leg `index` (HOST 604-662 [SRC]); PRIMARY_INTF = the vPC name."""
    n = index + 1
    pcid = str(parent_nv.get("PEER%d_PCID" % n, "")).strip()
    return {
        "PO_ID": vpc_po_name(pcid), "PRIMARY_INTF": vpc_name,
        "BPDUGUARD_ENABLED": parent_nv.get("BPDUGUARD_ENABLED", "true"),
        "PORTTYPE_FAST_ENABLED": parent_nv.get("PORTTYPE_FAST_ENABLED", "true"),
        "spanningTreePortType": parent_nv.get("spanningTreePortType", "no"),
        "MTU": parent_nv.get("MTU", "jumbo"), "SPEED": parent_nv.get("SPEED", "Auto"),
        "PVLAN_ALLOWED_VLANS": parent_nv.get("PEER%d_PVLAN_ALLOWED_VLANS" % n, "") or "",
        "PVLAN_NATIVE_VLAN": parent_nv.get("PEER%d_PVLAN_NATIVE_VLAN" % n, "") or "",
        "DESC": parent_nv.get("PEER%d_PO_DESC" % n, "") or "",
        "PORT_DUPLEX_MODE": parent_nv.get("PORT_DUPLEX_MODE", "auto"),
        "DISABLE_LACP_SUSPEND": parent_nv.get("DISABLE_LACP_SUSPEND", "false"),
        "ENABLE_LACP_VPC_CONV": parent_nv.get("ENABLE_LACP_VPC_CONV", "false"),
        "CONF": parent_nv.get("PEER%d_PO_CONF" % n, "") or "",
        "PVLAN_MODE": parent_nv.get("PVLAN_MODE", MODE_HOST),
        MAPPING_LIST: parent_nv.get(MAPPING_LIST, "") or "", ASSOCIATION_LIST: parent_nv.get(ASSOCIATION_LIST, "") or "",
        "ADMIN_STATE": parent_nv.get("ADMIN_STATE", "true"), "ENABLE_PFC": parent_nv.get("ENABLE_PFC", "false"),
        # The CORRECTED parent hands QOS_POLICY only with ENABLE_QOS true (qosPolicy; the AI/ML fallback is refused upstream).
        "ENABLE_QOS": parent_nv.get("ENABLE_QOS", "false"),
        "QOS_POLICY": (parent_nv.get("QOS_POLICY", "") or "") if str(parent_nv.get("ENABLE_QOS", "false")).strip().lower() == "true" else "",
        "qosStatsSuppressed": parent_nv.get("qosStatsSuppressed", "false"), "queuingStats": parent_nv.get("queuingStats", "false"),
        "QUEUING_POLICY": parent_nv.get("QUEUING_POLICY", "") or "", "aclFilter": parent_nv.get("aclFilter", "") or "",
    }


def vpc_leg_member_nv(parent_nv, index, vpc_name, current_nv, current_is_member=False):
    """nvPairs the parent hands to the member of leg `index` (HOST 727-760 [SRC]) with the same DESC/CONF/ADMIN_STATE
    inheritance as the regular port-channel member (po_member_nvpairs); `__PARENT` is the child Po's nvPairs plus the
    parent-level fields the member's CLI depends on. Never written by the module."""
    like = dict(vpc_leg_po_nv(parent_nv, index, vpc_name))
    like.update({
        "PC_MODE": parent_nv.get("PC_MODE", "active"), "CDP_ENABLE": parent_nv.get("CDP_ENABLE", "true"),
        "lldpTransmit": parent_nv.get("lldpTransmit", "false"), "lldpReceive": parent_nv.get("lldpReceive", "false"),
        "LACP_PORT_PRIO": parent_nv.get("LACP_PORT_PRIO", 32768), "LACP_RATE": parent_nv.get("LACP_RATE", "normal"),
        "COPY_DESC": parent_nv.get("COPY_DESC", "false"),
    })
    nv = po_member_nvpairs(like, current_nv, current_is_member=current_is_member)
    nv["PRIMARY_INTF"] = vpc_name
    return nv


def _render_vpc_po(nv):
    """Interface body of int_vpc_pvlan_po.add() (POVPC 59-170) for host mode: the regular port-channel PVLAN host body plus
    `vpc <id>` (PRIMARY_INTF). Values the model does not cover make the Model unmodeled, which refuses the deploy."""
    m = re.match(r"^vpc([0-9]+)$", _text(nv, "PRIMARY_INTF").lower())
    if not m or nv.get("PVLAN_MODE") not in PVLAN_MODES:  # the four submodes (POVPC 217-252 [SRC] = the regular Po body)
        return Model((), None, (), False)
    # VPC convergence (POVPC 292-293), PFC (300-302) and the port ACL (318-321) are rendered. Ingress QoS is rendered
    # as the CORRECTED child does (POVPC 305-309 with `type qos input`, the regular templates' line; QVPC-ENG patch 02). The INSTALLED
    # child renders `service-policy type ENABLE_QOS input <p>` (DEF-PVLAN-05): its expected configuration then disagrees and is refused.
    acl = _text(nv, "aclFilter")
    qos_on = _flag(nv, "ENABLE_QOS", "false")
    qos_policy = _text(nv, "QOS_POLICY")
    if (_flag(nv, "ENABLE_LACP_VPC_CONV", "false") not in ("true", "false") or _flag(nv, "ENABLE_PFC", "false") not in ("true", "false")
            or qos_on not in ("true", "false") or (qos_on == "true" and not _NATIVE_POLICY_NAME.match(qos_policy))
            or _flag(nv, "qosStatsSuppressed", "false") not in ("true", "false")
            or not (acl == "" or _NATIVE_POLICY_NAME.match(acl))):
        return Model((), None, (), False)
    base = _render_po_host(nv)
    if not base.modeled:
        return base
    scalars = set(base.scalars)
    scalars.add("vpc %s" % m.group(1))
    if _flag(nv, "ENABLE_LACP_VPC_CONV", "false") == "true":
        scalars.add("lacp vpc-convergence")
    if _flag(nv, "ENABLE_PFC", "false") == "true":
        scalars.update(("priority-flow-control mode on", "priority-flow-control watch-dog-interval on"))
    if acl:
        scalars.add("ip port access-group %s in" % acl)
    if qos_on == "true":
        scalars.add("service-policy type qos input %s%s" % (qos_policy, " no-stats" if _flag(nv, "qosStatsSuppressed", "false") == "true" else ""))
    return Model(scalars, base.list_kind, base.pairs, True)


def vpc_leg_models(parent_nv, index, vpc_name, member_nv, current_is_member):
    """((child policy, nv), (member policy, nv)) of one leg for a given parent nvPairs: the inputs of render()."""
    po_nv = vpc_leg_po_nv(parent_nv, index, vpc_name)
    return ((VPC_PO_POLICY, po_nv),
            (PO_MEMBER_POLICY, vpc_leg_member_nv(parent_nv, index, vpc_name, member_nv, current_is_member)))


def vpc_leg_cli_changes(pre_models, post_models):
    """True when the CLI model of the child Po or of the member differs between two states of one leg (render() of each side)."""
    for pre, post in zip(pre_models, post_models):
        a, b = render(*pre), render(*post)
        if not (a.modeled and b.modeled):
            return True
        if not same_state(a, b):
            return True
    return False


def vpc_combine(mode, decisions, expected=None, after_deploy=False):
    """The decision for a whole vPC from the per-leg decisions ("deploy"/"converged"/"refuse"), never from one leg.
    Returns (decision, problems). `after_deploy`: the deploy of THIS create/update was already sent and accepted in this invocation (the
    check_deploy safety re-deploy check); a peer that deploy applied is then "converged" and one it did not apply yet still needs "deploy",
    while for an update a peer predicted "converged" must still be converged. `mode`:
      create  every leg must be "deploy": a leg already converged is a state this request does not explain;
      update  each leg must show exactly what the models predict (`expected`, per leg, from the PREVIOUS and NEW models), so a
              leg that legitimately has no CLI change may stay converged while the other deploys;
      repeat  no change was requested: both legs "converged" (deployed) or both "deploy" (intent saved, not applied); a mix is a
              pre-existing partial state;
      delete  every leg must be "deploy" (the deletion is completed by the deploy; never converged)."""
    if len(decisions) != 2:
        return "refuse", ["the vPC needs exactly two leg decisions, got %d" % len(decisions)]
    bad = [i for i, d in enumerate(decisions) if d not in ("deploy", "converged")]
    if bad:
        return "refuse", ["peer %d: the gate did not accept the leg (%s)" % (i + 1, decisions[i]) for i in bad]
    if after_deploy and mode == "create":
        return ("deploy" if "deploy" in decisions else "converged"), []
    if after_deploy and mode == "update":
        if expected is None or len(expected) != 2:
            return "refuse", ["no expected result per peer was derived from the previous and new models"]
        off = [i for i in (0, 1) if decisions[i] != expected[i] and not (expected[i] == "deploy" and decisions[i] == "converged")]
        if off:
            return "refuse", ["peer %d shows %s after the deploy but this update predicts %s; the difference is not explained by the request"
                              % (i + 1, decisions[i], expected[i]) for i in off]
        return ("deploy" if "deploy" in decisions else "converged"), []
    if mode in ("create", "delete"):
        off = [i for i, d in enumerate(decisions) if d != "deploy"]
        if off:
            return "refuse", ["peer %d is already converged, which this %s request does not explain; nothing is deployed" % (i + 1, mode) for i in off]
        return "deploy", []
    if mode == "update":
        if expected is None or len(expected) != 2:
            return "refuse", ["no expected result per peer was derived from the previous and new models"]
        off = [i for i in (0, 1) if decisions[i] != expected[i]]
        if off:
            return "refuse", ["peer %d shows %s but this update predicts %s; the difference is not explained by the request"
                              % (i + 1, decisions[i], expected[i]) for i in off]
        return ("deploy" if "deploy" in decisions else "converged"), []
    if mode == "repeat":
        if decisions[0] != decisions[1]:
            return "refuse", ["pre-existing partial state: peer 1 is %s and peer 2 is %s" % (decisions[0], decisions[1])]
        return decisions[0], []
    return "refuse", ["unknown vPC gate mode %r" % (mode,)]


def vpc_response_class(resp, sno, name):
    """Class of the answer to the vPC parent CREATE: "accepted" | "failed" | "unknown". Never a verdict on the vPC.
      * HTTP 200 "OK": the contract the module already applies to every create (generic path);
      * HTTP 207 "Multi-Status": accepted ONLY when every item is SUCCESS and a SUCCESS item names the parent in one of the two
        entity forms the shared helper admits (`serial~name`, `serial:name`, with the pair serial) -- PROVISIONAL, from the Po
        precedent, not measured for a vPC; an item per child is NOT required;
      * a 207 with an ERROR item is "failed"; any other shape (unknown item type, missing parent, no list) is "unknown".
    "accepted" only says the controller took the request: both legs are still gated and read back."""
    if not isinstance(resp, dict):
        return "unknown"
    if resp.get("RETURN_CODE") == 200 and resp.get("MESSAGE") == "OK":
        return "accepted"
    if resp.get("RETURN_CODE") != 207 or resp.get("MESSAGE") != "Multi-Status":
        return "failed"
    data = resp.get("DATA")
    if not isinstance(data, list) or not all(isinstance(i, dict) for i in data) or not data:
        return "unknown"
    types = {str(i.get("reportItemType", "")).upper() for i in data}
    if "ERROR" in types:
        return "failed"
    if types != {"SUCCESS"}:
        return "unknown"
    return "accepted" if not modify_outcome_problems(resp, [(sno, name)]) else "unknown"


# Child nvPairs (POVPC declarations) that the new companions reach, with the child template's default.
_VPC_CHILD_COMPANION_DEFAULTS = (
    ("spanningTreePortType", "no"), ("PORT_DUPLEX_MODE", "auto"), ("DISABLE_LACP_SUSPEND", "false"), ("ENABLE_LACP_VPC_CONV", "false"),
    ("ENABLE_PFC", "false"), ("QUEUING_POLICY", ""), ("queuingStats", "false"), ("aclFilter", ""),
    # Ingress QoS handed by the corrected parent
    ("ENABLE_QOS", "false"), ("QOS_POLICY", ""), ("qosStatsSuppressed", "false"),
)
# Object names (ACL, queuing policy-map) are compared EXACTLY, as the parent reconciliation keeps them; only the boolean and
# enum keys above keep their case-insensitive form, and so does the QoS policy-map name.
_VPC_CHILD_EXACT_NAME_KEYS = frozenset(("aclFilter", "QUEUING_POLICY", "QOS_POLICY"))


def vpc_child_differences(child_nv, expected_po_nv):
    """Keys on which a stored child Po intent differs from the child the parent's intent implies (a leg that does not follow its
    parent is an incoherent, partial state). Compared only on what decides the CLI of the leg; unreadable values count as
    differences. Pure."""
    if not isinstance(child_nv, dict):
        return ["nvPairs"]
    diffs = []
    try:
        for key in ("PVLAN_MODE", "ADMIN_STATE", "DESC", "BPDUGUARD_ENABLED", "PORTTYPE_FAST_ENABLED", "MTU"):
            if _po_norm(key, child_nv.get(key, "")) != _po_norm(key, expected_po_nv.get(key, "")):
                diffs.append(key)
        # RC1: the speed and the freeform the parent hands to the child (an absent SPEED is the template's Auto).
        if (_text(child_nv, "SPEED") or "Auto") != (_text(expected_po_nv, "SPEED") or "Auto"):
            diffs.append("SPEED")
        if not _freeform_same(child_nv.get("CONF", ""), expected_po_nv.get("CONF", "")):
            diffs.append("CONF")
        # Both lists and the per-peer PVLAN native/allowed decide the CLI of the leg in the other submodes.
        for key in (ASSOCIATION_LIST, MAPPING_LIST):
            if pairs_from_wire(child_nv.get(key, "") or "", key) != pairs_from_wire(expected_po_nv.get(key, "") or "", key):
                diffs.append(key)
        if not native_equal(child_nv.get(NATIVE_VLAN, "") or "", expected_po_nv.get(NATIVE_VLAN, "") or ""):
            diffs.append(NATIVE_VLAN)
        if not allowed_equal(child_nv.get(ALLOWED_VLANS, "") or "", expected_po_nv.get(ALLOWED_VLANS, "") or ""):
            diffs.append(ALLOWED_VLANS)
        # The companions the parent now lets an operator set also decide the CLI of the leg. A child that does not carry
        # one is compared at the template default (an absent nvPair is the template's own value, never a difference by itself).
        for key, default in _VPC_CHILD_COMPANION_DEFAULTS:
            have_v = str("" if child_nv.get(key, default) is None else child_nv.get(key, default)).strip()
            want_v = str("" if expected_po_nv.get(key, default) is None else expected_po_nv.get(key, default)).strip()
            if key not in _VPC_CHILD_EXACT_NAME_KEYS:
                have_v, want_v = have_v.lower(), want_v.lower()
            if have_v != want_v:
                diffs.append(key)
    except PvlanError:
        diffs.append("list")
    for key in ("PO_ID", "PRIMARY_INTF"):
        if key in child_nv and str(child_nv.get(key, "")).strip().lower() != str(expected_po_nv.get(key, "")).strip().lower():
            diffs.append(key)
    return diffs


vpc_same = _vpc_same  # public name for the module's post-deploy readback


def po_intent_same(key, have_nv, want_nv):
    """RC2 (L2): one nvPair of the port-channel host intent, read back after the deploy, against the intent that was sent: the existing
    _po_same comparison (CONF order-insensitive, SPEED normalized text), an absent key read as the template's own value."""
    default = _PO_ABSENT_DEFAULT.get(key, "")
    return _po_same(key, (have_nv or {}).get(key, default), (want_nv or {}).get(key, default))


def vpc_transition_problems(pre, post):
    """Problems of the IDEAL pending of the transition between two Models of one interface (any list kind): every added line, the
    withdrawal of every removed line, every added or removed pair. The pre-deploy gate validates a real pending with the same rules; when
    even the ideal pending cannot satisfy them, the transition could only be refused AFTER the intent was written, so the caller refuses
    it BEFORE (known limit of the shared validator: `shutdown` <-> `no shutdown` is one line that adds and withdraws at once)."""
    if not (pre.modeled and post.modeled):
        return ["the transition is not modeled"]
    # A withdrawn negative-form line is written in its NX-OS positive form (`no lldp transmit` -> `lldp transmit`), unless
    # that positive form is itself an intended line (`no shutdown` -> `shutdown` keeps its previous treatment, unchanged).
    body = sorted(post.scalars - pre.scalars) + [
        line[3:] if line.startswith("no ") and line[3:] not in post.scalars else "no " + line
        for line in sorted(pre.scalars - post.scalars)]
    # The list line of each submode (the same keywords the templates render, POVPC 229-252 [SRC]).
    fmt = _VPC_LIST_FORMAT.get(post.list_kind)
    if pre.list_kind == post.list_kind and fmt:
        body += [fmt % p for p in sorted(post.pairs - pre.pairs)]
        body += ["no " + fmt % p for p in sorted(pre.pairs - post.pairs)]
    return validate_transition(body, pre, post)


_VPC_LIST_FORMAT = {
    MODE_HOST: "switchport private-vlan host-association %d %d",
    MODE_PROMISCUOUS: "switchport private-vlan mapping %d %d",
    MODE_TRUNK_PROMISCUOUS: "switchport private-vlan mapping trunk %d %d",
    MODE_TRUNK_SECONDARY: "switchport private-vlan association trunk %d %d",
}


# ================================================================== member readback against the expected per-peer model
# Fields that DETERMINE the CLI of a vPC member (int_port_channel_pvlan_member, MEMBER:109-205 [SRC]); PRIMARY_INTF, INTF_NAME, PTP and
# INTF_PTP are metadata/identity, never compared as wire values (PRIMARY_INTF is only an identity check when present).
VPC_MEMBER_KEYS = ("PO_ID", "PC_MODE", "PVLAN_MODE", "CDP_ENABLE", "lldpTransmit", "lldpReceive", "LACP_PORT_PRIO", "LACP_RATE", "DESC",
                   "CONF", "ADMIN_STATE")
_VPC_MEMBER_REQUIRED = ("PO_ID", "PC_MODE", "PVLAN_MODE", "ADMIN_STATE")
_VPC_MEMBER_DEFAULT = {"CDP_ENABLE": "true", "lldpTransmit": "false", "lldpReceive": "false", "LACP_PORT_PRIO": "32768",
                       "LACP_RATE": "normal", "DESC": "", "CONF": ""}
_VPC_MEMBER_LOWER = ("PO_ID", "PC_MODE", "PVLAN_MODE", "CDP_ENABLE", "lldpTransmit", "lldpReceive", "ADMIN_STATE", "LACP_RATE")


def _member_value(key, value):
    if isinstance(value, bool):
        value = "true" if value else "false"
    if not isinstance(value, (str, int)):
        return None
    text = str(value).strip()
    return text.lower() if key in _VPC_MEMBER_LOWER else text


def vpc_member_differences(have_nv, expected_nv):
    """Differences between the member's authoritative nvPairs and the member model EXPECTED for its peer (empty = same). `expected_nv` comes
    from the frozen pre-state (po_member_nvpairs: DESC/CONF/ADMIN_STATE inherited from the member BEFORE the write), never from the state
    being verified. A required field that is missing or malformed is a difference, not a success; an optional one that is missing takes the
    template default. Types and case are normalised; wire metadata (PRIMARY_INTF aside) is ignored. Pure."""
    if not isinstance(have_nv, dict):
        return ["the member's nvPairs are unreadable"]
    diffs = []
    for key in VPC_MEMBER_KEYS:
        raw = have_nv.get(key)
        if raw is None:
            if key in _VPC_MEMBER_REQUIRED:
                diffs.append("%s is missing" % key)
                continue
            raw = _VPC_MEMBER_DEFAULT[key]
        value = _member_value(key, raw)
        if value is None:
            diffs.append("%s is malformed (%s)" % (key, type(raw).__name__))
            continue
        wanted = _member_value(key, expected_nv.get(key, _VPC_MEMBER_DEFAULT.get(key, "")))
        if value != wanted:
            diffs.append("%s is %r, expected %r" % (key, value, wanted))
    primary = have_nv.get("PRIMARY_INTF")
    wanted_primary = expected_nv.get("PRIMARY_INTF")
    if primary not in (None, "") and wanted_primary and str(primary).strip().lower() != str(wanted_primary).strip().lower():
        diffs.append("PRIMARY_INTF is %r, expected %r" % (primary, wanted_primary))
    return diffs


def vpc_released_member_differences(have_nv, contract_nv, policy=TRUNK_HOST_POLICY):
    """Differences between a RELEASED member (after a vPC deletion) and the explicit release contract stored in the leg (PO_RELEASED_MEMBER_NV,
    a direct int_trunk_host, shut, no freeform commands). Judged on the CLI model of both sides (so every modeled field counts) plus the
    contract's own fields by name; residual PVLAN/channel-group fields, an unmodelable member or unreadable nvPairs are differences. No history.
    `policy` is the released template (int_trunk_host, unchanged default, or int_routed_host with released_member_contract())."""
    if not isinstance(have_nv, dict):
        return ["the released member's nvPairs are unreadable"]
    diffs = []
    for key in ("PO_ID", "PVLAN_MODE", "PC_MODE", "ASSOCIATION_LIST", "MAPPING_LIST"):
        if str(have_nv.get(key, "") or "").strip() not in ("", '{"ASSOCIATION_LIST":[]}', '{"MAPPING_LIST":[]}'):
            diffs.append("residual PVLAN/channel-group field %s=%r" % (key, have_nv.get(key)))
    for key in sorted(contract_nv):
        if key == "ALLOWED_VLANS":
            same = allowed_equal(have_nv.get(key, "") or "", contract_nv[key] or "") if str(have_nv.get(key, "") or "").strip() else False
        elif key == "NATIVE_VLAN":
            same = native_equal(have_nv.get(key, "") or "", contract_nv[key] or "")
        else:
            same = str(have_nv.get(key, "") if have_nv.get(key) is not None else "").strip().lower() == str(contract_nv[key]).strip().lower()
        if not same:
            diffs.append("%s is %r, the release contract requires %r" % (key, have_nv.get(key), contract_nv[key]))
    got, want = render(policy, have_nv), render(policy, contract_nv)
    if not got.modeled:
        diffs.append("the released member's configuration cannot be modeled (a required field is missing or outside the model)")
    elif want.modeled and not same_state(got, want) and not diffs:
        diffs.append("the released member's CLI model differs from the contract: %s" % (_difference(got, want),))
    return diffs
