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


# PO-HOST-E1-OFFLINE: grammars of the regular port-channel host policy and of its PVLAN member
# policy. Kept in their OWN tables so the Ethernet tables, VOCABULARY_POLICIES and
# DEFAULT_VOCABULARY above stay byte-for-byte what E6 defined: no Ethernet decision can change.
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
    )
    + _PO_LIST_GRAMMAR,
    # The member's own template lines + the parent's 'Inherited Commands' int_eth child on the member (HOST:507-560).
    PO_MEMBER_POLICY: (
        r"switchport",
        r"switchport mode private-vlan (host|promiscuous|trunk promiscuous|trunk secondary)",
        # G3 (H1, NDFC 12.6.0.267, controller preview MEASURED; H1 was never deployed): the pending carries the COMMAND
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
# VPC-HOST-E1-OFFLINE: the vPC child policy keeps its OWN tables, filled in the vPC section below, so PO_VOCABULARY_POLICIES and
# every Po/Ethernet decision stay what they were.
_VPC_GRAMMAR = {}
_VPC_NAMESPACES = {}

# G6 (TS prepared member, EXP-1 MEASURED on one Ethernet member, NX-OS 10.5(5), NDFC 12.6.0.267): the ONLY device lines a member
# PREPARED as access or routed may hold when it joins a trunk secondary port-channel. Access (int_access_host): `shutdown`,
# `spanning-tree port type edge`, `mtu 9216`; routed (int_routed_host): `no switchport`, `mtu 9216` (shutdown is the L3 default
# and is NOT shown). Their field namespaces include switchport/ip/ipv6/vrf so any other line there is uninterpretable (refused).
# Own table: VOCABULARY_POLICIES, PO_VOCABULARY_POLICIES and DEFAULT_VOCABULARY stay byte-for-byte what G5 defined.
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
    if policy == PO_HOST_POLICY:
        return _render_po_host(nv)
    if policy == PO_MEMBER_POLICY:
        return _render_po_member(nv)
    if policy == VPC_PO_POLICY:
        return _render_vpc_po(nv)
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


def assess_target(body, entry, name, desired, vocabulary=None, absent_ok=False, member_force=None, member_inherit=None):
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
    `member_force` (G3, port-channel member creation only) applies po_member_force_transition() first.
    `member_inherit` (G5: the NAME of the port-channel of an existing member, given only when that port-channel's own pending
    changes) reads the member's device state through po_member_inherited_state() against the port-channel's running stanza
    in the same entry: an empty member pending is then a deploy carried by the parent, not a refusal."""
    if not desired.modeled:
        return "refuse", ["the intended state of %s is not modeled" % name]
    vocabulary = vocabulary or DEFAULT_VOCABULARY
    for key in ("runningConfig", "expectedConfig"):
        if not isinstance(entry.get(key), list):
            return "refuse", ["the fresh preview carries no %s, so the device state of %s is unknown" % (key, name)]
    rc, running = interface_stanza(entry["runningConfig"], name)
    xc, expected = interface_stanza(entry["expectedConfig"], name)
    if absent_ok and rc == 0 and xc == 1:
        # PO-HOST-E1-OFFLINE: an interface that is created by this very operation has no running
        # stanza yet. That is accepted ONLY here, from a readable runningConfig list and exactly
        # one expected stanza; a duplicated or missing expected stanza is still a refusal.
        observed = Model((), None, (), True)
    elif rc != 1 or xc != 1:
        return "refuse", ["the fresh preview holds %d running and %d expected stanzas for %s" % (rc, xc, name)]
    else:
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
    inherited = False
    if member_inherit:
        prc, parent_running = interface_stanza(entry["runningConfig"], member_inherit)
        parent_observed = cli_model(parent_running, vocabulary) if prc == 1 else None
        observed, inherited = po_member_inherited_state(observed, desired, parent_observed)
    if not body:
        if same_state(observed, desired):
            return ("deploy" if inherited else "converged"), []
        return "refuse", ["the pending for %s is empty but the device differs from the intended state: %s" % (name, _difference(observed, desired))]
    body, observed, problems = po_member_force_transition(body, observed, desired, member_force)
    if problems:
        return "refuse", problems
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


# ================================================================== regular port-channel, four PVLAN modes
# PO-HOST-E1-OFFLINE -> PO G1. Everything below is derived from the
# captured templates int_port_channel_pvlan_host / int_port_channel_pvlan_member (their template contract and
# the port-channel validation contract) and from the helpers above; no value comes from a controller measurement of a
# port-channel. Scope (anything else is refused before a write): ONE port-channel with exactly ONE physical member;
# creation; update of the PVLAN lists/scalars without changing pvlan_mode or the member; identical repetition.
PO_PROFILE_KEYS = frozenset((
    "mode", "pvlan_mode", "pvlan_association", "pvlan_mapping", "native_vlan", "allowed_vlans",
    "members", "pc_mode", "description", "admin_state",
))
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
    ("LACP_PORT_PRIO", 32768),  # declared `integer`: sent as an integer, not as a string (E2 decision, UNMEASURED)
    ("LACP_RATE", "normal"),
    ("QUEUING_POLICY", ""),
    ("queuingStats", "false"),
    ("ADMIN_STATE", "true"),
)
# PVLAN_NATIVE_VLAN is declared `integer` 1-4094 on BOTH the Ethernet and the port-channel template (G1-CORR-1 §2a).
# Neutral value: the empty string (E2). A non-empty native VLAN is sent as a string of digits, the form MEASURED as
# accepted for the integer-declared Ethernet field over the same legacy transport (E6 live). Whether the port-channel
# create/modify path accepts it, and how it reads it back, is NOT measured: first measured by the trunk roles (G1 gate).
PO_NATIVE_NEUTRAL = ""
PO_NAME = re.compile(r"^port-channel[1-9][0-9]{0,3}$", re.IGNORECASE)
PO_PHYSICAL_MEMBER = re.compile(r"^ethernet[0-9]+/[0-9]+$", re.IGNORECASE)
# Every nvPair the host template declares (29, TEMPLATE_CONTRACT_G1 §2) plus the bookkeeping keys the controller adds.
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
    """Reasons a port-channel PVLAN request is outside the G1 delivery (empty = in scope).
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
        if not isinstance(members, list) or len(members) != 1:
            reasons.append(
                "exactly one member is implemented for a port-channel in mode 'pvlan' (adding or removing "
                "members is not)")
        elif not isinstance(members[0], str) or not PO_PHYSICAL_MEMBER.match(members[0].strip()):
            reasons.append("the member must be one physical Ethernet interface name, for example Ethernet1/9")
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
    return reasons


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
    nv["CONF"] = ""
    nv["PVLAN_MODE"] = mode
    trunk = mode in TRUNK_MODES
    nv[ALLOWED_VLANS] = raw.get("allowed_vlans", "") if trunk else ""
    nv[NATIVE_VLAN] = raw.get("native_vlan", PO_NATIVE_NEUTRAL) if trunk else PO_NATIVE_NEUTRAL
    active = active_list_key(mode)
    field = _po_list_field(mode)
    pairs = requested_pairs(field, raw[field]) if raw.get(field) is not None else []
    nv[MAPPING_LIST] = pairs_to_wire(MAPPING_LIST, pairs) if active == MAPPING_LIST and pairs else ""
    nv[ASSOCIATION_LIST] = pairs_to_wire(ASSOCIATION_LIST, pairs) if active == ASSOCIATION_LIST and pairs else ""
    return nv


def _po_norm(key, value):
    """Comparable form of one HAVE/WANT nvPair of the port-channel host policy."""
    if value is None:
        return None
    text = str(value).strip()
    if key in _PO_BOOL_KEYS:
        return text.lower()
    if key == "MEMBER_INTERFACES":
        # G6 (EXP-1, MEASURED): a port-channel created through Manage stores its member as `e1/8`, the legacy path as
        # `Ethernet1/8`. Both name the same port; a token that is not one explicit port stays as written (never equal to a port).
        return tuple(sorted(po_member_canonical(m) or m.strip().lower() for m in text.split(",") if m.strip()))
    if key == "PO_ID":
        return text.lower()
    return text


def _po_same(key, have_value, want_value):
    if key in (MAPPING_LIST, ASSOCIATION_LIST):
        return pairs_from_wire(have_value or "", key) == pairs_from_wire(want_value or "", key)
    if key == NATIVE_VLAN:
        return native_equal(have_value or "", want_value or "")
    if key == ALLOWED_VLANS:
        return allowed_equal(have_value or "", want_value or "")
    return _po_norm(key, have_value) == _po_norm(key, want_value)


_PO_ABSENT_DEFAULT = dict(list(PO_TEMPLATE_DEFAULTS) + [
    ("DESC", ""), ("CONF", ""), (ALLOWED_VLANS, ""), (NATIVE_VLAN, ""), (MAPPING_LIST, ""), (ASSOCIATION_LIST, "")])


def reconcile_po(state, raw, ifname, have_policy, have_nv):
    """Decision for ONE port-channel host WANT against its HAVE:
    {nv, update, creates, changed, blocked, new_secondaries, members}.

      * HAVE absent (have_policy None) -> creation with the explicit payload (members and the active list required);
      * HAVE is this policy, same pvlan_mode, same single member -> update:
          - `merged`: every omitted field keeps its HAVE value; the active list is the UNION of HAVE and request;
          - `replaced`: the explicit payload (omitted fields = template declarations), members kept from HAVE;
        equality (normalized) is a no-op returning the HAVE nvPairs untouched;
      * a change of pvlan_mode or of the member set, another policy, unclassifiable HAVE fields -> refused.
    The promiscuous partial-removal guard of the Ethernet path applies unchanged: on a port-channel its controller
    behaviour is NOT measured, so the protection is kept rather than assumed unnecessary (contract)."""
    out = {"nv": None, "update": False, "creates": False, "changed": {}, "blocked": [], "new_secondaries": [], "members": None}
    mode = raw["pvlan_mode"]
    field = _po_list_field(mode)
    active = active_list_key(mode)
    if have_policy is None:
        if not po_members(raw):
            out["blocked"].append("members is required to create a port-channel: exactly one existing physical member")
        if raw.get(field) is None or not requested_pairs(field, raw[field]):
            out["blocked"].append("%s is required to create a port-channel in pvlan_mode %s" % (field, mode))
        if out["blocked"]:
            return out
        nv = po_host_nvpairs(raw, ifname)
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
    have_members = _po_norm("MEMBER_INTERFACES", have_nv.get("MEMBER_INTERFACES", ""))
    if len(have_members) != 1:
        out["blocked"].append("the existing port-channel has %d members; exactly one is implemented" % len(have_members))
    if "members" in raw and raw["members"] is not None and _po_norm("MEMBER_INTERFACES", ",".join(po_members(raw))) != have_members:
        out["blocked"].append(
            "changing the members of an existing PVLAN port-channel is not implemented (requested %s, current %s)"
            % (", ".join(po_members(raw)), ", ".join(have_members)))
    if out["blocked"]:
        return out
    members_text = have_nv.get("MEMBER_INTERFACES", "")
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
    else:
        nv = po_host_nvpairs(raw, have_nv.get("PO_ID", ifname), members=members_text)
        if "PTP" in have_nv and str(have_nv["PTP"]).strip().lower() in ("true", "false"):
            nv["PTP"] = have_nv["PTP"]
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
    (HOST:507-526,555-560 [SRC]): the resolved MTU when not the switch default, then the PVLAN native/allowed/list lines.
    Speed/negotiate/duplex lines depend on device capability (Util.*) and are not modeled: _po_scalars_ok refuses them."""
    lines = []
    if _flag(po_nv, "MTU", "jumbo") == "jumbo":
        lines.append("mtu 9216")
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
# (`switchport mode trunk / allowed vlan none / edge trunk / mtu 9216`) and SHUTDOWN. G4: the controller does NOT release it
# that way by itself -- MEASURED (HR, NDFC 12.6.0.267): after the mark-delete the member became a new int_trunk_host with
# ADMIN_STATE "true" although FAB1 HOST_INTF_ADMIN_STATE is "false" and the member was down. The module therefore sets
# ADMIN_STATE "false" explicitly before any deploy (po_released_member_payload); the pre-deploy gate still requires the
# controller's expected member configuration to be exactly this model.
PO_RELEASED_MEMBER_NV = {
    "MTU": "jumbo", "SPEED": "Auto", "BPDUGUARD_ENABLED": "no", "PORTTYPE_FAST_ENABLED": "true",
    "ALLOWED_VLANS": "none", "NATIVE_VLAN": "", "ADMIN_STATE": "false", "DESC": "", "CONF": "",
}


# G4: controller metadata of an interface policy read back with its nvPairs. Classified (BOOKKEEPING, also used by the
# measured E6 update path, which sends HAVE minus these keys): never sent back, and a readback may change, add or drop them.
PO_RELEASE_METADATA = frozenset(BOOKKEEPING)


# G4-R1: the ONLY mark-delete answer accepted as a confirmed deletion of one PVLAN port-channel. MEASURED (HR, NDFC
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


# G5 (live host finding F-HR-deployed, G4R1 run, NDFC 12.6.0.267, MEASURED): after the mark-delete of a DEPLOYED
# port-channel the controller keeps listing it until the deploy -- interface summary entry with markDeleted true,
# complianceStatus "NA" and ONE underlay policy `interface_delete` (entity and source = the port-channel); the policy list
# holds that policy with deleted true; the port-channel's own detail answers an empty list. The released member is already
# a standalone int_trunk_host (ADMIN_STATE "true") and the pending carries `no interface port-channelN`. A port-channel that
# was never deployed disappears at once (HR of G2). Only this measured form counts as "deleted, awaiting the deploy".
PO_DELETE_PENDING_POLICY = "interface_delete"


# E5 (L1-E4 live F2, MEASURED for the child port-channel of a deleted vPC, NDFC 12.6.0.267): the same marked-for-deletion form, but the
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


def po_released_member_payload(nv, ifname, serial, fabric):
    """The ONE legacy interface/modify payload of the G4 member release: the released int_trunk_host with ALL its current
    writable nvPairs (the fresh read, minus PO_RELEASE_METADATA) and only ADMIN_STATE changed to "false". Never the
    generic seven-key default payload; never a stale copy."""
    out = dict((k, v) for k, v in nv.items() if k not in PO_RELEASE_METADATA)
    out["ADMIN_STATE"] = "false"
    intf = {"interfaceType": "INTERFACE_ETHERNET", "serialNumber": serial, "ifName": ifname, "fabricName": fabric, "nvPairs": out}
    return {"policy": TRUNK_HOST_POLICY, "interfaces": [intf]}


def po_released_member_readback_problems(before, after):
    """Differences between the released member's writable nvPairs before the G4 modify and its fresh readback. Only
    ADMIN_STATE may change (and must now be "false"); a writable key that disappears, changes value or appears is a
    problem; PO_RELEASE_METADATA is the only tolerated difference."""
    if not isinstance(after, dict):
        return ["the member readback carries no nvPairs"]
    problems = []
    if str(after.get("ADMIN_STATE", "")).strip().lower() != "false":
        problems.append("ADMIN_STATE reads back %r, not 'false'" % (after.get("ADMIN_STATE"),))
    keys = (set(before) | set(after)) - PO_RELEASE_METADATA - {"ADMIN_STATE"}
    for key in sorted(keys):
        if key not in after:
            problems.append("writable nvPair %s was lost" % key)
        elif key not in before:
            problems.append("writable nvPair %s appeared (%r)" % (key, after[key]))
        elif str(after[key]) != str(before[key]):
            problems.append("writable nvPair %s changed %r -> %r" % (key, before[key], after[key]))
    return problems


# G6: nvPairs of a PREPARED access/routed member that would render configuration; each must hold its neutral value (the values
# MEASURED on the EXP-1 prepared members). Anything else is configuration this contract does not model: refused before any write.
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
# The live child policies the controller keeps on a member prepared as routed, each with the member itself as source (MEASURED,
# EXP-1 branch R: routed_interface 450, interface_mtu 452, shut_interface 458); they disappeared when the port-channel was created.
PO_ROUTED_SELF_CHILDREN = frozenset(("routed_interface", "interface_mtu", "shut_interface"))
PO_TS_TRUNK_MEMBER_INCIDENT = (
    "a member in switchport mode trunk (%s) cannot join a trunk secondary port-channel: NX-OS rejects `channel-group N force` "
    "with 'PVLAN TRUNK SEC config present' (measured on NX-OS 10.5(5): deploy 500, partial). Known "
    "incident pending engineering; prepare the member explicitly as access (%s) or routed (%s) before the creation, the module "
    "does not convert it" % (TRUNK_HOST_POLICY, PO_ACCESS_BASELINE_POLICY, PO_ROUTED_BASELINE_POLICY))


def po_member_baseline_problems(baseline_policy, baseline_nv, mode=None):
    """Reasons an existing Ethernet policy cannot be the baseline of a PVLAN member in this
    delivery. The member template would turn the port ADMIN-UP when it inherits no `false`.
    G6: for pvlan_mode trunk secondary ONLY, a member explicitly PREPARED as access or routed is admitted (EXP-1 measured), with
    its rendering nvPairs neutral; a trunk member is refused as the known incident. The other modes keep the trunk-only contract."""
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
    if str(baseline_nv.get("ADMIN_STATE", "")).strip().lower() != "false":
        problems.append(
            "the member is not administratively down (ADMIN_STATE %r); the PVLAN member template inherits "
            "the member's state and would leave or bring it up" % (baseline_nv.get("ADMIN_STATE"),))
    if str(baseline_nv.get("CONF", "") or "").strip():
        problems.append("the member carries freeform CONF, which the member template would drop")
    return problems


def _po_scalars_ok(nv):
    """True when `nv` holds only values the G1 delivery models (everything else is refused)."""
    mode = nv.get("PVLAN_MODE")
    trunk = mode in TRUNK_MODES
    return (
        _text(nv, "SPEED") in ("", "Auto")
        and _flag(nv, "MTU", "jumbo") in ("jumbo", "default")
        and _text(nv, "spanningTreePortType") in ("", "no")
        and _flag(nv, "BPDUGUARD_ENABLED", "true") in ("true", "false", "no")
        and _flag(nv, "ENABLE_ORPHAN_PORT", "false") == "false"
        and _flag(nv, "DISABLE_LACP_SUSPEND", "false") == "false"
        and _text(nv, "PORT_DUPLEX_MODE") in ("", "auto")
        and not _text(nv, "QUEUING_POLICY")
        and not _text(nv, "CONF")
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
    bpdu = _flag(nv, "BPDUGUARD_ENABLED", "true")
    if bpdu == "true":
        s.add("spanning-tree bpduguard enable")
    elif bpdu == "false":
        s.add("spanning-tree bpduguard disable")
    if _flag(nv, "PORTTYPE_FAST_ENABLED", "true") == "true":
        s.add("spanning-tree port type edge trunk")
    if _text(nv, "DESC"):
        s.add("description %s" % _text(nv, "DESC"))
    s.add("no shutdown" if _flag(nv, "ADMIN_STATE", "true") == "true" else "shutdown")
    try:
        pairs = _po_pairs(nv, mode)
    except PvlanError:
        return Model((), None, (), False)
    return Model(s, mode, pairs, True)


# G3: the controller's view of `channel-group N force mode M` on a physical member, MEASURED in the H1 PREVIEW (host,
# NDFC 12.6.0.267, the H1 measured fixture): the member pending held only
# `no spanning-tree port type edge trunk`, `channel-group 502 force mode active` and `shutdown`, while the controller's
# expected member configuration became `channel-group 502 mode active`, `mtu 9216`, `shutdown`, `switchport`,
# `switchport mode private-vlan host`, `switchport private-vlan host-association 2210 2212`. So, in the controller's model,
# the PVLAN mode and list lines arrive with `force` and the member's own trunk switchport lines go away with it.
# H1 was never deployed: what the SWITCH ends up with after that pending is NOT observed (NX-OS `force` semantics is
# the expectation); live acceptance must compare the device's running configuration. Only the measured preview effect
# is modeled, and only for the modes measured (other modes: temporary refusal, not a statement about device support).
PO_FORCE_MEASURED_MODES = frozenset((MODE_HOST,))
# G5 (NEXT_MODES, design decision): the same effect is applied to the
# other three modes as an explicit INFERENCE, NOT a measurement: none of them has a controller preview or a switch
# observation of a member joining through `force`. It rests on (a) the measured host preview above, (b) the captured
# templates -- the parent's 'Inherited Commands' int_eth child renders on every member the same parent-owned lines in
# all four modes (mode, list pairs and, for the trunk modes, PVLAN native/allowed; HOST:428-462,507-560) -- and (c) the
# controller expected member those templates produce. The live gate still compares the controller's expected member
# with the intent and validates the rest of the pending; the first live case of each mode measures the real form.
PO_FORCE_INFERRED_MODES = frozenset((MODE_PROMISCUOUS, MODE_TRUNK_PROMISCUOUS, MODE_TRUNK_SECONDARY))
# The member lines the force carries FROM THE PARENT, besides the mode line and the list pairs (G5: inferred for the
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
    """'measured' (host), 'inferred' (G5: the other three PVLAN modes) or None (not a PVLAN mode)."""
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
        the trunk switchport lines, `no switchport` (G6: routed, EXP-1 measured) and any previous PVLAN line, which the force
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
        # G6 (EXP-1 branch R, MEASURED): a routed port is down by the L3 default without a `shutdown` line (adminStatus 2, ADMIN_STATE
        # false), so cli_model's restored `no shutdown` is not its state; the admin line must then come from the pending itself.
        scalars.discard("no shutdown")
    scalars |= {"switchport", "switchport mode private-vlan %s" % member_force["mode"],
                po_member_channel_group(member_force["po_number"], member_force["pc_mode"])}
    scalars |= set(line for line in post.scalars if _PO_FORCE_PARENT_LINE.match(line))
    forced = Model(scalars, post.list_kind, post.pairs, pre.modeled, pre.foreign)
    return [line for line in body if line != command], forced, []


def po_member_force_withdrawal(body, po_number, pc_mode):
    """(body, problems) of a member LEAVING its deleted port-channel. G5 (live host finding F-HR-deployed, MEASURED): the
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
    G5 (live host finding F-H4, MEASURED on H4, host, NDFC 12.6.0.267): after a host-association update the pending held
    ONLY the port-channel block (withdraw the old pair + the full stanza with the new one), the controller's expected member
    held the new pair, the member's running the old one and the member pending NOTHING: NX-OS inherits the port-channel's
    PVLAN configuration on the member (observed on the device at H1 creation; after an update deploy it is the same NX-OS
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
    if _text(nv, "CONF") or _flag(nv, "CDP_ENABLE", "true") != "true" or _flag(nv, "lldpTransmit", "false") != "false" \
            or _flag(nv, "lldpReceive", "false") != "false" or _text(nv, "LACP_PORT_PRIO") != "32768" \
            or _text(nv, "LACP_RATE") != "normal" or not _po_scalars_ok(parent):
        return Model((), None, (), False)
    pc_mode = _text(nv, "PC_MODE")
    if pc_mode not in PO_PC_MODES:
        return Model((), None, (), False)
    s = {"switchport", "switchport mode private-vlan %s" % mode}
    s.add(po_member_channel_group(m.group(1), pc_mode))
    if _text(nv, "DESC"):
        s.add("description %s" % _text(nv, "DESC"))
    s.add("no shutdown" if _flag(nv, "ADMIN_STATE", "true") == "true" else "shutdown")
    s.update(po_inherited_lines(parent))
    try:
        pairs = _po_pairs(parent, mode)
    except PvlanError:
        return Model((), None, (), False)
    return Model(s, mode, pairs, True)


# ------------------------------------------------------------------ PO-HOST-E2-CONFLICTS: requested-set membership identity
# One explicit port per token, in the forms the existing module path already accepts and normalises for Ethernet names
# (dcnm_intf_get_if_name keeps the digits of `Ethernet1/7`, `eth1/7`, `e1/7`). Anything else -- a range such as
# `Ethernet1/5-8`, a port-channel, free text -- is NOT resolved here: the caller refuses it when it could hide a conflict.
_MEMBER_PORT = re.compile(r"^(?:ethernet|eth|e)?\s*([0-9]+/[0-9]+(?:/[0-9]+)?)$", re.IGNORECASE)


def po_member_canonical(token):
    """`ethernetX/Y` (lower case) for one explicit physical port token in any accepted spelling (`Ethernet1/8`, `eth1/8`,
    `e1/8`), else None. Comparison only: outbound payloads keep the controller's own spelling."""
    found = _MEMBER_PORT.match(str(token or "").strip())
    return "ethernet" + found.group(1) if found else None


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


# ================================================================== VPC-HOST-E1-OFFLINE: vPC PVLAN host (int_vpc_pvlan_host)
# Everything below is pure (no read, no transport) and ADDITIVE: no Ethernet or port-channel table, function
# or decision above changes. Contract sources, labelled so a fixture is never mistaken for a measurement:
#   [SRC]  the installed templates captured 2026-10-07 (int_vpc_pvlan_host / int_vpc_pvlan_po / int_port_channel_pvlan_member;
#          provenance limited: installed templates captured, NOT a confirmed factory SMU). HOST n / POVPC n cite their bodies.
#   [INF]  inferred from those bodies (for example that the child policies are written when the parent intent is saved).
#   [UNK]  not known until the first live case (L1): the summary/policy-list shape of the vPC itself, the 207/deploy bodies of
#          a vPC, the release of the members after a vPC delete.
VPC_HOST_POLICY = "int_vpc_pvlan_host"
VPC_PO_POLICY = "int_vpc_pvlan_po"
VPC_NAME = re.compile(r"^vpc([1-9][0-9]{0,3})$", re.IGNORECASE)
VPC_PROFILE_KEYS = frozenset((
    "mode", "pvlan_mode", "pvlan_association", "peer1_members", "peer2_members", "peer1_pcid", "peer2_pcid", "pc_mode",
    "peer1_description", "peer2_description", "admin_state",
    # VPC-MODES-E1: the other three submodes of the same parent template (HOST 192-229 [SRC]): the mapping list of the promiscuous
    # modes and, for the trunk modes only (IsShow PVLAN_MODE!=promiscuous && !=host), the PER-PEER PVLAN native/allowed VLANs.
    "pvlan_mapping", "peer1_allowed_vlans", "peer2_allowed_vlans", "peer1_native_vlan", "peer2_native_vlan",
))
# VPC-MODES-E1: public per-peer fields -> the parent nvPair suffix they set on the controller's n-th serial.
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
# E5 (L1-E4 live F1, MEASURED): a created vPC parent carries `createVpc` = "true" in its nvPairs. It is NOT a field of the installed
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
_VPC_GRAMMAR[VPC_PO_POLICY] = _PO_GRAMMAR[PO_HOST_POLICY] + (r"vpc [0-9]+",)
_VPC_NAMESPACES[VPC_PO_POLICY] = _PO_NAMESPACES[PO_HOST_POLICY] + ("vpc",)
VPC_VOCABULARY_POLICIES = tuple(sorted(_VPC_GRAMMAR))


def vpc_id(ifname):
    """Digits of a vPC interface name ('vPC10' -> '10'), or None."""
    m = VPC_NAME.match(str(ifname or "").strip())
    return m.group(1) if m else None


def vpc_not_implemented(profile, ifname):
    """Reasons a vPC PVLAN request is outside the delivery (empty = in scope). Decided from the RAW profile, before any default or
    coercion and before any read. VPC-MODES-E1: the four PVLAN submodes of int_vpc_pvlan_host; per submode only the fields its template
    shows (association: host/trunk secondary; mapping: promiscuous/trunk promiscuous; per-peer native/allowed: the trunk modes) and the
    template's own list limits. Still deferred: more or fewer than one member per peer, a PCID different from the vPC id, an empty list,
    freeform commands, member/mode changes."""
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
            if not isinstance(members, list) or len(members) != 1:
                reasons.append("%s: exactly one member per peer is implemented for a vPC in mode 'pvlan'" % key)
            elif not isinstance(members[0], str) or not PO_PHYSICAL_MEMBER.match(members[0].strip()):
                reasons.append("%s must be one physical Ethernet interface name, for example Ethernet1/9" % key)
        pcid = peer + "_pcid"
        if pcid not in profile or profile.get(pcid) is None:
            reasons.append("%s is required and must equal the vPC id (a different port-channel number is not implemented)" % pcid)
        elif isinstance(profile[pcid], bool) or not isinstance(profile[pcid], int) or (vid is not None and str(profile[pcid]) != vid):
            reasons.append("%s must equal the vPC id %s (a different port-channel number is not implemented)" % (pcid, vid))
        desc = peer + "_description"
        if desc in profile and profile[desc] is not None:
            value = profile[desc]
            if not isinstance(value, str) or not 1 <= len(value) <= 254 or "\n" in value:
                reasons.append("%s must be a single-line string of 1-254 characters" % desc)
        reasons += _vpc_peer_trunk_errors(profile, peer, mode)
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
    return reasons


def _vpc_peer_trunk_errors(profile, peer, mode):
    """VPC-MODES-E1: errors of the per-peer PVLAN native/allowed fields of one peer (raw profile). Same value rules as the regular
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


def vpc_pair_view(raw, combined, playbook_serials):
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
            "member": members[0].strip() if isinstance(members, list) and members else None,
            "pcid": raw.get("peer%d_pcid" % peer),
            "desc": raw.get("peer%d_description" % peer),
            # VPC-MODES-E1: per-peer PVLAN trunk native/allowed of THIS serial (None = omitted).
            "native": raw.get("peer%d_native_vlan" % peer),
            "allowed": raw.get("peer%d_allowed_vlans" % peer),
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
        nv["PEER%d_PO_CONF" % n] = ""
        # VPC-MODES-E1: per-peer native/allowed only in the trunk modes; a native VLAN is sent as a string of digits (the form measured
        # accepted for the integer-declared regular Po field, TP1/TS1 live); neutral '' otherwise.
        nv["PEER%d_PVLAN_ALLOWED_VLANS" % n] = (leg.get("allowed") or "") if trunk else ""
        nv["PEER%d_PVLAN_NATIVE_VLAN" % n] = (leg.get("native") or PO_NATIVE_NEUTRAL) if trunk else PO_NATIVE_NEUTRAL
    field = _po_list_field(mode)
    active = active_list_key(mode)
    pairs = requested_pairs(field, raw[field]) if raw.get(field) is not None else []
    nv[MAPPING_LIST] = pairs_to_wire(MAPPING_LIST, pairs) if active == MAPPING_LIST and pairs else ""
    nv[ASSOCIATION_LIST] = pairs_to_wire(ASSOCIATION_LIST, pairs) if active == ASSOCIATION_LIST and pairs else ""
    return nv


def _vpc_norm(key, value):
    if value is None:
        return None
    text = str(value).strip()
    if key in _VPC_BOOL_KEYS:
        return text.lower()
    if key in ("PEER1_MEMBER_INTERFACES", "PEER2_MEMBER_INTERFACES"):
        # E4: the same port in any accepted spelling (`Ethernet1/8`, `e1/8`) compares equal, as for the regular port-channel (G6, EXP-1).
        return tuple(sorted(po_member_canonical(m) or m.strip().lower() for m in text.split(",") if m.strip()))
    if key in ("PEER1_PCID", "PEER2_PCID", "LACP_PORT_PRIO"):
        return text
    return text


def _vpc_same(key, have_value, want_value):
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
        if key in ("PEER1_PO_DESC", "PEER1_PVLAN_NATIVE_VLAN", "PEER1_PVLAN_ALLOWED_VLANS"):
            legs.add(0)
        elif key in ("PEER2_PO_DESC", "PEER2_PVLAN_NATIVE_VLAN", "PEER2_PVLAN_ALLOWED_VLANS"):
            legs.add(1)
        else:
            legs.update((0, 1))
    return sorted(legs)


def reconcile_vpc(state, raw, ifname, legs, have_policy, have_nv):
    """Decision for ONE vPC PVLAN WANT against its HAVE: {nv, update, creates, changed, blocked, members, ask_legs, new_secondaries}.

      * HAVE absent -> creation with the explicit payload (one member per peer and the submode's list are required);
      * HAVE is this policy, the SAME submode, one explicit member per peer, PCID = vPC id, no stored CONF -> update. `merged` keeps
        every omitted field from HAVE (the active list is the union); `replaced` states the complete model (members and PCIDs from
        HAVE). An equal request is a no-op;
      * another policy, a submode/member/PCID change, stored CONF, unclassifiable HAVE fields, the promiscuous partial removal (the
        protection kept from the measured Ethernet defect), or a change that reaches ONE peer only (the unilateral update of a vPC is
        NOT implemented: its modify behaviour is unmeasured) -> blocked.
    VPC-MODES-E1: submodes promiscuous / trunk promiscuous (MAPPING_LIST) and trunk secondary (ASSOCIATION_LIST) next to host, with the
    per-peer PVLAN native/allowed of the trunk modes. `new_secondaries` (trunk secondary) are typed by the caller before any write."""
    out = {"nv": None, "update": False, "creates": False, "changed": {}, "blocked": [], "members": None, "ask_legs": [],
           "new_secondaries": []}
    vid = vpc_id(ifname)
    mode = raw.get("pvlan_mode", MODE_HOST)
    field = _po_list_field(mode)
    active = active_list_key(mode)
    if have_policy is None:
        if any(leg["member"] is None for leg in legs):
            out["blocked"].append("peer1_members and peer2_members are required to create a vPC: exactly one existing physical member per peer")
        if not raw.get(field):
            out["blocked"].append("%s is required to create a vPC in pvlan_mode %s" % (field, mode))
        if out["blocked"]:
            return out
        nv = vpc_host_nvpairs(raw, ifname, legs)
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
        if unresolved or len(names) != 1:
            out["blocked"].append("the existing vPC has %d member entr(ies) on peer %d; exactly one explicit member per peer is implemented"
                                  % (len(names) + len(unresolved), n))
        have_members.append(sorted(names)[0] if len(names) == 1 else None)
        if str(have_nv.get("PEER%d_PCID" % n, "")).strip() != (vid or ""):
            out["blocked"].append("PEER%d_PCID %r differs from the vPC id %s; a different port-channel number is not implemented"
                                  % (n, have_nv.get("PEER%d_PCID" % n), vid))
        if str(have_nv.get("PEER%d_PO_CONF" % n, "") or "").strip():
            out["blocked"].append("the vPC stores freeform commands on peer %d (PEER%d_PO_CONF); they are not implemented, and "
                                  "the template would run its freeform checks on add and delete" % (n, n))
    for leg in legs:
        have_member = have_members[leg["index"]]
        if leg["member"] is not None and have_member is not None and (po_member_canonical(leg["member"]) or leg["member"].lower()) != have_member:
            out["blocked"].append("changing the member of an existing vPC is not implemented (peer %d: requested %s, current %s)"
                                  % (leg["index"] + 1, leg["member"], have_member))
    if out["blocked"]:
        return out
    # peerN_* of the playbook are bound to the serial that owns them; the controller-order nvPairs come from the legs.
    merged = state == "merged"
    current = pairs_from_wire(have_nv.get(active, "") or "", active)
    requested = requested_pairs(field, raw[field]) if raw.get(field) is not None else None
    desired = sorted(set(current) | set(requested or [])) if merged else sorted(set(requested or []))
    out["blocked"] += limit_errors(mode, desired)
    if not desired:
        # the host text of E5 is kept byte-for-byte; the promiscuous modes name their mapping
        out["blocked"].append("an empty %s is not implemented for a vPC" % ("association" if field == "pvlan_association" else "mapping"))
    if promiscuous_partial_removal(have_mode, mode, current, desired):
        out["blocked"].append(
            "removing secondary VLAN(s) %s from a promiscuous mapping that keeps other secondaries is blocked (protection kept from the "
            "measured Ethernet defect; its behaviour on a vPC is NOT measured). Remove the whole vPC instead"
            % ", ".join("%d/%d" % p for p in sorted(set(current) - set(desired))))
    if out["blocked"]:
        return out
    members = [have_nv.get("PEER1_MEMBER_INTERFACES", ""), have_nv.get("PEER2_MEMBER_INTERFACES", "")]
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
            if mode in TRUNK_MODES:
                if leg.get("native") is not None:
                    nv["PEER%d_PVLAN_NATIVE_VLAN" % (leg["index"] + 1)] = leg["native"]
                if leg.get("allowed") is not None:
                    nv["PEER%d_PVLAN_ALLOWED_VLANS" % (leg["index"] + 1)] = leg["allowed"]
        nv["PVLAN_MODE"] = mode
    else:
        nv = vpc_host_nvpairs(raw, ifname, legs, members=members)
        for key in VPC_CONTROLLER_METADATA:
            if key in have_nv and have_nv[key] not in ("", None):
                nv[key] = have_nv[key]
        if "PTP" in have_nv and str(have_nv["PTP"]).strip().lower() in ("true", "false"):
            nv["PTP"] = have_nv["PTP"]
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
    if len(ask) == 1:
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
        "ENABLE_QOS": parent_nv.get("ENABLE_QOS", "false"), "QOS_POLICY": parent_nv.get("QOS_POLICY", "") or "",
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
    if not m or nv.get("PVLAN_MODE") not in PVLAN_MODES:  # VPC-MODES-E1: the four submodes (POVPC 217-252 [SRC] = the regular Po body)
        return Model((), None, (), False)
    if (_flag(nv, "ENABLE_LACP_VPC_CONV", "false") != "false" or _flag(nv, "ENABLE_PFC", "false") != "false"
            or _flag(nv, "ENABLE_QOS", "false") != "false" or _text(nv, "aclFilter")):
        return Model((), None, (), False)
    base = _render_po_host(nv)
    if not base.modeled:
        return base
    scalars = set(base.scalars)
    scalars.add("vpc %s" % m.group(1))
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


def vpc_combine(mode, decisions, expected=None):
    """The decision for a whole vPC from the per-leg decisions ("deploy"/"converged"/"refuse"), never from one leg.
    Returns (decision, problems). `mode`:
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


def vpc_leg_residue(policies, vpc_name, po_name, member, member_detail_nv):
    """Reasons a leg is NOT clean after a vPC deletion (empty = clean). `policies` is the leg's fresh live-policy list.
    The released member legitimately keeps ONE direct int_trunk_host policy (its baseline): that is NOT residue. Residue is
    any live policy that is a vPC child (source = the vPC), names the removed vPC or Po as its entity, is not the single
    direct baseline of the member, or still holds the PVLAN member policy. No history is needed: the baseline is the explicit
    contract (direct int_trunk_host, source empty, administratively down, no freeform CONF)."""
    vname, pname, mname = str(vpc_name).lower(), str(po_name).lower(), str(member).lower()
    live = [p for p in policies if p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true"]
    reasons = []
    own = []
    for p in live:
        entity, template, source = str(p.get("entityName", "")).lower(), p.get("templateName"), str(p.get("source", "")).lower()
        tag = "%s/%s/%s" % (p.get("entityName"), template, p.get("source"))
        if source == vname:
            reasons.append("a policy owned by the removed vPC is still live: %s" % tag)
        elif entity in (pname, vname):
            reasons.append("a policy for the removed %s is still live: %s" % ("port-channel" if entity == pname else "vPC", tag))
        elif entity == mname:
            own.append(p)
        elif source == pname:
            reasons.append("a policy claimed by the removed port-channel is still live: %s" % tag)
    baseline = [p for p in own if p.get("templateName") == TRUNK_HOST_POLICY and str(p.get("source", "")) == ""
                and str(p.get("entityType", "")).upper() == "INTERFACE"]
    if len(own) != 1 or len(baseline) != 1:
        reasons.append("the member does not hold exactly one direct %s policy (%s)" % (
            TRUNK_HOST_POLICY, ", ".join(sorted("%s/%s" % (p.get("templateName"), p.get("source")) for p in own)) or "none"))
    if isinstance(member_detail_nv, dict):
        if str(member_detail_nv.get("ADMIN_STATE", "")).strip().lower() != "false":
            reasons.append("the released member is not administratively down")
        if str(member_detail_nv.get("CONF", "") or "").strip():
            reasons.append("the released member carries freeform CONF")
    return reasons


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
        # VPC-MODES-E1: both lists and the per-peer PVLAN native/allowed decide the CLI of the leg in the other submodes.
        for key in (ASSOCIATION_LIST, MAPPING_LIST):
            if pairs_from_wire(child_nv.get(key, "") or "", key) != pairs_from_wire(expected_po_nv.get(key, "") or "", key):
                diffs.append(key)
        if not native_equal(child_nv.get(NATIVE_VLAN, "") or "", expected_po_nv.get(NATIVE_VLAN, "") or ""):
            diffs.append(NATIVE_VLAN)
        if not allowed_equal(child_nv.get(ALLOWED_VLANS, "") or "", expected_po_nv.get(ALLOWED_VLANS, "") or ""):
            diffs.append(ALLOWED_VLANS)
    except PvlanError:
        diffs.append("list")
    for key in ("PO_ID", "PRIMARY_INTF"):
        if key in child_nv and str(child_nv.get(key, "")).strip().lower() != str(expected_po_nv.get(key, "")).strip().lower():
            diffs.append(key)
    return diffs


vpc_same = _vpc_same  # public name for the module's post-deploy readback


def vpc_transition_problems(pre, post):
    """Problems of the IDEAL pending of the transition between two Models of one interface (any list kind): every added line, the
    withdrawal of every removed line, every added or removed pair. The pre-deploy gate validates a real pending with the same rules; when
    even the ideal pending cannot satisfy them, the transition could only be refused AFTER the intent was written, so the caller refuses
    it BEFORE (known limit of the shared validator: `shutdown` <-> `no shutdown` is one line that adds and withdraws at once)."""
    if not (pre.modeled and post.modeled):
        return ["the transition is not modeled"]
    body = sorted(post.scalars - pre.scalars) + ["no " + line for line in sorted(pre.scalars - post.scalars)]
    # VPC-MODES-E1: the list line of each submode (the same keywords the templates render, POVPC 229-252 [SRC]).
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


# ================================================================== VPC-HOST-E2-READBACK: member readback against the expected per-peer model
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


def vpc_released_member_differences(have_nv, contract_nv):
    """Differences between a RELEASED member (after a vPC deletion) and the explicit release contract stored in the leg (PO_RELEASED_MEMBER_NV,
    a direct int_trunk_host, shut, no freeform commands). Judged on the CLI model of both sides (so every modeled field counts) plus the
    contract's own fields by name; residual PVLAN/channel-group fields, an unmodelable member or unreadable nvPairs are differences. No history."""
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
    got, want = render(TRUNK_HOST_POLICY, have_nv), render(TRUNK_HOST_POLICY, contract_nv)
    if not got.modeled:
        diffs.append("the released member's configuration cannot be modeled (a required field is missing or outside the model)")
    elif want.modeled and not same_state(got, want) and not diffs:
        diffs.append("the released member's CLI model differs from the contract: %s" % (_difference(got, want),))
    return diffs
