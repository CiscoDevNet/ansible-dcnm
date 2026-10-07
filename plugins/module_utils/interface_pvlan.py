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

PROFILE_KEYS = frozenset(("mode", "pvlan_mode", "pvlan_association", "pvlan_mapping", "native_vlan", "allowed_vlans") + tuple(c[0] for c in COMPANIONS))
# Keys dcnm_intf_copy_config injects into its profile copy; never user input.
INJECTED_KEYS = frozenset(("fabric", "sno", "ifname", "policy"))

SPEED_VALUES = ("Auto", "10Mb", "100Mb", "1Gb", "2.5Gb", "5Gb", "10Gb", "25Gb", "40Gb", "50Gb", "100Gb", "200Gb", "400Gb", "800Gb")
# Freeform lines that would manage PVLAN or switchport mode outside the structured fields.
_CONF_FORBIDDEN = re.compile(r"private-vlan|^\s*(no\s+)?switchport\b", re.IGNORECASE)


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
    """Strict 'N', 'N-M' comma list -> sorted list of ints. Descending, degenerate,
    overlapping or duplicate input is refused so duplicates cannot vanish in a set."""
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
        if m.group(2) and high <= low:
            raise PvlanError("%s range %r is not ascending" % (field, part))
        for v in range(low, high + 1):
            if not 1 <= v <= 4094:
                raise PvlanError("%s %d is outside 1-4094" % (field, v))
            if v in seen:
                raise PvlanError("%s repeats VLAN %d" % (field, v))
            seen.add(v)
            out.append(v)
    return sorted(out)


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
    return errors


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
        elif kind == "bpdu" and value not in ("true", "false", "no"):
            errors.append("bpdu_guard must be 'true', 'false' or 'no'")
        elif kind == "mtu" and value not in ("jumbo", "default"):
            errors.append("mtu must be 'jumbo' or 'default'")
        elif kind == "speed" and value not in SPEED_VALUES:
            errors.append("speed must be one of: %s" % ", ".join(SPEED_VALUES))
        elif kind == "duplex" and value not in ("auto", "full", "half"):
            errors.append("duplex must be 'auto', 'full' or 'half'")
        elif kind == "conf":
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                errors.append("cmds must be a list of strings")
            elif any(_CONF_FORBIDDEN.search(x) for x in value):
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
    secondary per primary. Applied to raw input AND again after a merged union."""
    pairs = sorted(set(pairs))
    if mode == MODE_HOST and len(pairs) > 1:
        return ["pvlan_mode host allows at most one association"]
    if mode == MODE_PROMISCUOUS and len({p for p, _s in pairs}) > 1:
        return ["pvlan_mode promiscuous allows a single primary VLAN in its mapping"]
    if mode == MODE_TRUNK_SECONDARY:
        primaries = [p for p, _s in pairs]
        if len(primaries) != len(set(primaries)):
            return ["pvlan_mode trunk secondary allows one secondary VLAN per primary VLAN"]
    return []


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
        return "\n".join(value)
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
    """The demonstrated non-trunk defect (G5 PU3/PX1): retained promiscuous mapping that would
    lose an existing pair while a mapping remains. Mixed remove+add is included on purpose."""
    return have_mode == MODE_PROMISCUOUS and want_mode == MODE_PROMISCUOUS and bool(have_pairs) and bool(want_pairs) and bool(set(have_pairs) - set(want_pairs))


# ------------------------------------------------------------------ reconciliation
def reconcile(state, raw_profile, ifname, have_policy, have_nv):
    """WANT vs authoritative HAVE for one int_pvlan_host target.

    raw_profile: the user's raw profile (presence = key in dict; already validated).
    have_policy/have_nv: current policy and nvPairs, or (None, None) when the target has no
    readable direct policy (the caller refuses that before calling).

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
                extra = [l for l in raw_profile[key] if l not in have_lines]
                value = "\n".join(have_lines + extra) if extra else have_raw
        elif merged and same_policy and have_raw is not None:
            value = have_raw
        else:
            value = default
        if same_policy and have_raw is not None and _companion_equal(kind, value, have_raw):
            value = have_raw
        nv[nvp] = value

    # ---- preservation-only, never owned here
    if have_nv:
        for nvp in PRESERVE_ALWAYS + (PRESERVE_SAME_POLICY if same_policy else ()):
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


_ABSENT_DEFAULT = dict([(c[1], c[3]) for c in COMPANIONS] + [(ASSOCIATION_LIST, ""), (MAPPING_LIST, ""), (NATIVE_VLAN, ""), (ALLOWED_VLANS, "")])


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

# ------------------------------------------------------------------ owned CLI vocabulary (E3)
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


class Vocabulary(object):
    """What one requested transition owns. owns(line): the operation may change/withdraw it.
    interferes(line): a line it does NOT own falls in a field namespace it does own, so the
    model cannot interpret the device state there."""

    def __init__(self, policies, freeform=()):
        self.policies = tuple(sorted(set(p for p in policies if p in _GRAMMAR)))
        grammar = [g for p in self.policies for g in _GRAMMAR[p]]
        self._grammar = re.compile("^(?:%s)$" % "|".join(grammar)) if grammar else None
        self.freeform = frozenset(freeform)
        self._prefixes = tuple(sorted(set(n for p in self.policies for n in _NAMESPACES[p])))

    def owns(self, line):
        return line in self.freeform or bool(self._grammar and self._grammar.match(line))

    def interferes(self, line):
        bare = line[3:] if line.startswith("no ") else line
        return any(bare == p or bare.startswith(p + " ") for p in self._prefixes)


def _conf_lines(policy, nv):
    if policy not in _GRAMMAR or not isinstance(nv, dict):
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
    follows the installed template's add() (sha256 99dc8f0a788d..., captured 2026-09-26/27 and
    2026-10-01 on the same ND90 build). Values whose rendering depends on device capability or
    fabric settings (non-default speed, AI/ML QoS fallback, PFC watchdog, storm-control levels,
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
    return Model((), None, (), False)


def _flag(nv, key, default):
    value = nv.get(key, default)
    return default if value is None else str(value).strip().lower()


def _text(nv, key):
    value = nv.get(key, "")
    return "" if value is None else str(value).strip()


def _pvlan_values_modeled(nv):
    if _text(nv, "SPEED") not in ("", "Auto"):
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


def validate_transition(body, pre, post):
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
    # pending (G5 TU1) withdraws the old mapping through the mode change alone.
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
      * measured success (G5/G6): HTTP 200, DATA {"message": "Interface deployed successfully",
        "value": [{"serialNumber", "IfName"}, ...]} naming every deployed interface;
      * documented benign notice (module source, not measured in G1-G6): HTTP 200, DATA a list
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


# ------------------------------------------------------------------ device authority (E2)
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


def assess_target(body, entry, name, desired, vocabulary=None):
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
        which a foreign device command can never be withdrawn."""
    if not desired.modeled:
        return "refuse", ["the intended state of %s is not modeled" % name]
    vocabulary = vocabulary or DEFAULT_VOCABULARY
    for key in ("runningConfig", "expectedConfig"):
        if not isinstance(entry.get(key), list):
            return "refuse", ["the fresh preview carries no %s, so the device state of %s is unknown" % (key, name)]
    rc, running = interface_stanza(entry["runningConfig"], name)
    xc, expected = interface_stanza(entry["expectedConfig"], name)
    if rc != 1 or xc != 1:
        return "refuse", ["the fresh preview holds %d running and %d expected stanzas for %s" % (rc, xc, name)]
    observed = cli_model(running, vocabulary)
    controller = cli_model(expected, vocabulary)
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
    if not body:
        if same_state(observed, desired):
            return "converged", []
        return "refuse", ["the pending for %s is empty but the device differs from the intended state: %s" % (name, _difference(observed, desired))]
    problems = validate_transition(body, observed, desired)
    return ("refuse", problems) if problems else ("deploy", [])


# ------------------------------------------------------------------ interface summary policy (E4)
# MEASURED (NDFC 12.6.0.267, FAB1 interface/detail, 72 entries): no entry carries a top-level `policy`;
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
