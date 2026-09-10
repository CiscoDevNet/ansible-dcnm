# Thin additive registry-driven engine (Phase 1 Monday slice). Offline. No live.
#
# Consumes ONLY the packaged static binding table (gie_binding_table). It does not read the
# investigation evidence dir or NDFC template files. It is ADDITIVE: it acts only on
# REGISTERED profile keys the caller authored EXPLICITLY; an omitted key is never emitted and
# never acquires a new default. NDFC executes parent-template/child effects; the engine only
# contributes the parent nvPair.
#
# The engine OWNS, for every registered binding: explicit-presence, binding resolution, type
# validation (validator type from binding metadata) and supported-version parent-nvPair
# transport. An explicit value on an unsupported/unknown/malformed version fails closed by
# default. The one exact OSPF-MD binding is the sole exception: its proven module-level
# capability/HAVE reconciliation owns that path, so the engine withholds the nvPair there.
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    registered_profile_keys,
    resolve_binding,
    PROVENANCE_SHA256,
)

# nvPair transport mechanisms understood by the engine.
GIE_MECH_PASSTHROUGH = "passthrough"
GIE_MECH_CHILD_PTI = "child_pti"

# The ONE exact binding whose unsupported-version handling is delegated to the module's proven
# capability gate + HAVE reconciliation (withhold, do NOT fail). This is a narrow, per-binding
# compatibility identifier: it must NOT be generalized to `mechanism == child_pti`. Any other
# binding — including a future ordinary child_pti binding — follows the default policy and
# fails closed on an unsupported/unknown/malformed version.
GIE_OSPF_MD_COMPAT_BINDING = (
    "int_fabric_loopback_11_1",
    "ENABLE_OSPF_AUTH_MESSAGE_DIGEST",
)

# --- Generic same-parent HAVE carry-forward (drift fix) --------------------------------------
# CONFIRMED MECHANISM (this reproduction; NOT asserted as a universal rule for every template): on a
# fabric-loopback state:merged update the module builds a SPARSE modify payload (its loopback builder
# emits only a subset of the template's nvPairs). NDFC re-applies the policy template on
# /interface/modify and RESETS every writable nvPair the payload omitted -- observed drift:
#   PRIORITY 301->500, REPLICATION_MODE Ingress->Multicast, LINK_STATE_ROUTING_TAG/OSPF_AREA_ID -> gone.
# The metadata nvPairs the module never sends survived unchanged (NDFC owns them).
#
# Safe fix: on a SAME-PARENT merged update, carry the EXACT current HAVE value forward into the sent
# payload for nvPairs the builder omitted, so NDFC keeps them. The carried value is always the exact
# value NDFC returned in the GET (a round-trip / "leave as-is" assertion) -- never a default or guess
# -- so it cannot introduce a wrong value, produces no public diff and is idempotent. Two classes are
# DERIVED-and-DOCUMENTED exclusions (never carried):
#   (1) NDFC-managed read-only / identity metadata (survived the modify unchanged regardless of the
#       payload, so echoing is unnecessary and could be input-rejected):
GIE_READONLY_METADATA_NVPAIRS = frozenset({
    "FABRIC_NAME",
    "POLICY_ID",
    "POLICY_DESC",
    "MARK_DELETED",
    "INTF_NAME",
})
#   (2) the OSPF-MD feature domain (incl. key material), owned by the module's dedicated OSPF-MD path:
GIE_OSPF_MD_DOMAIN_NVPAIRS = frozenset({
    "ENABLE_OSPF_AUTH_MESSAGE_DIGEST",
    "OSPF_AUTH_KEY",
    "OSPF_AUTH_KEY_ID",
    "ospfAuthKeychainName",
})

# Registered binding "type" -> validate_list_of_dicts validator type. Native values are
# preserved (no stringification); an unknown type fails closed.
_TYPE_TO_VALIDATOR = {
    "boolean": "bool",
    "enum": "str",
    "string": "str",
    "integer": "int",
}

_VALIDATOR_TO_NATIVE_TYPE = {
    "bool": bool,
    "str": str,
    "int": int,
}


class GieBindingError(Exception):
    """Fail-closed engine condition (e.g. an unknown registered binding type)."""


def _is_native_type(value, native_type):
    """Accept the registered native type, INCLUDING its subclasses.

    Ansible does not hand a module plain ``str``: a value that came from a playbook arrives
    as ``AnsibleUnicode``, a ``str`` subclass. An exact ``type(value) is native_type`` check
    therefore rejects every string a real playbook can supply, while unit tests that pass a
    literal ``str`` keep passing -- which is exactly how that defect stayed invisible.

    ``bool`` and ``int`` still must not be interchangeable: ``isinstance(True, int)`` is True
    in Python, so a plain isinstance check would let a boolean satisfy an integer binding and
    reach NDFC as ``1``. Each is therefore pinned explicitly.
    """
    if native_type is bool:
        return isinstance(value, bool)
    if native_type is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, native_type)


def gie_version_supported(ndfc_version, min_version):
    """Four-segment >= compare; fail closed (False) for unknown/malformed versions.

    Compares as many segments as `min_version` specifies (matches _ndfc_version_gte).
    """
    if not ndfc_version:
        return False
    try:
        required = tuple(int(x) for x in str(min_version).split("."))
        current = tuple(int(x) for x in str(ndfc_version).split(".")[: len(required)])
        current = current + (0,) * (len(required) - len(current))
        return current >= required
    except (ValueError, AttributeError, TypeError):
        return False


def gie_validator_type(binding_type):
    """Map a registered binding type to the validate_list_of_dicts validator type.

    Fail closed (GieBindingError) on an unknown type; no silent default.
    """
    vt = _TYPE_TO_VALIDATOR.get(binding_type)
    if vt is None:
        raise GieBindingError(
            "unsupported registered binding type {0!r}; no template metadata was queried "
            "and no change was sent".format(binding_type)
        )
    return vt


def gie_validate_binding_value(
    parent_template, profile_key, value, value_source="explicit"
):
    """Validate a value against one exact packaged binding.

    The registered ``type``, ``valid_values`` and length bounds describe the **input
    contract**: what an operator may write in a playbook. They are enforced in full for
    ``value_source="explicit"``.

    They are NOT the **state contract**. A value read back from the controller is whatever
    NDFC holds, and NDFC's encoding legitimately differs from the input encoding:

      * ``ACL_FILTER`` comes back as ``""`` when no ACL is configured -- a perfectly valid
        state, but shorter than the registered ``min_length`` of 1;
      * booleans come back as the strings ``"true"`` / ``"false"``, not as ``bool``.

    Applying the input contract to those values made ``state: overridden`` fail on any host
    interface that was explicitly declared, because the carry-forward reads them from HAVE.
    Carrying such a value forward is safe -- it is a round-trip "leave as-is" assertion of
    what the controller already has, so it cannot introduce a wrong value.

    For ``value_source="have"`` the contract still applies in full, minus exactly TWO
    exemptions, each one backed by a value NDFC was measured to return on a freshly
    deployed fabric:

      1. a **boolean** binding also accepts the strings ``"true"`` / ``"false"``. NDFC
         encodes booleans that way on read-back (``DISABLE_LLDP == "false"``); the action
         plugin's schema documents the same round-trip.
      2. a **plain string** binding (one with no ``valid_values``) also accepts ``""``.
         That is how NDFC encodes "unset" (``ACL_FILTER == ""`` when no ACL is
         configured), and it is precisely what ``min_length`` was rejecting.

    Everything else is unchanged, deliberately. Enum membership is still enforced, so a
    value outside ``valid_values`` never reaches a later full-payload update -- and the
    ``""`` exemption is scoped to non-enum bindings so an empty enum still fails closed.
    Carrying a measured encoding forward is a round-trip "leave as-is" assertion and cannot
    introduce a wrong value; relaxing further would be inventing tolerance for encodings
    that have never been observed.

    Why this matters: applying the input contract to these two encodings made
    ``state: overridden`` abort on any explicitly declared host interface, which is every
    real deployment.

    The error deliberately omits the rejected value.
    """
    source_label = (
        "authoritative controller value"
        if value_source == "have"
        else "explicit value"
    )
    binding = resolve_binding(parent_template, profile_key)
    if binding is None:
        raise GieBindingError(
            "no exact registered binding for {0!r} on parent {1!r}; no change was sent".format(
                profile_key, parent_template
            )
        )
    validator_type = gie_validator_type(binding["type"])
    native_type = _VALIDATOR_TO_NATIVE_TYPE[validator_type]
    if value_source == "have":
        # (1) NDFC returns booleans as strings.
        if native_type is bool and value in ("true", "false"):
            return value
        # (2) NDFC returns "" for an unset plain string. Scoped to non-enum bindings so an
        #     empty value for an enum still fails closed.
        if native_type is str and value == "" and not binding.get("valid_values"):
            return value
    if not _is_native_type(value, native_type):
        raise GieBindingError(
            "{0} for {1!r} on parent {2!r} has an invalid native type; no change "
            "was sent".format(source_label, profile_key, parent_template)
        )
    valid_values = binding.get("valid_values")
    if valid_values and value not in valid_values:
        raise GieBindingError(
            "{0} for {1!r} on parent {2!r} is outside the registered choices; no "
            "change was sent".format(source_label, profile_key, parent_template)
        )
    # Registered length constraints (reviewed registry, e.g. ACL_FILTER 1..64). Applied to
    # string bindings only; like every other check here the message omits the value.
    if isinstance(value, str):
        min_length = binding.get("min_length")
        max_length = binding.get("max_length")
        if min_length is not None and len(value) < min_length:
            raise GieBindingError(
                "{0} for {1!r} on parent {2!r} is shorter than the registered minimum "
                "length {3}; no change was sent".format(
                    source_label, profile_key, parent_template, min_length
                )
            )
        if max_length is not None and len(value) > max_length:
            raise GieBindingError(
                "{0} for {1!r} on parent {2!r} is longer than the registered maximum "
                "length {3}; no change was sent".format(
                    source_label, profile_key, parent_template, max_length
                )
            )
    return value


def gie_all_registered_keys():
    """Every public profile key known to the packaged registry, across all parents."""
    return {b["profile_key"] for b in BINDING_TABLE}


def gie_nvpair_keymap():
    """Return the registry-owned nvPair -> public profile-key mapping.

    The legacy comparator uses this mapping to distinguish an explicitly authored value
    from an omitted value.  Fail closed if the packaged table ever assigns one nvPair name
    to different public keys; such ambiguity must be fixed in the generated registry before
    the module can compare state safely.
    """
    out = {}
    for binding in BINDING_TABLE:
        nvpair = binding["parent_nvpair"]
        profile_key = binding["profile_key"]
        if nvpair in out and out[nvpair] != profile_key:
            raise GieBindingError(
                "ambiguous registered nvPair {0!r}: maps to both {1!r} and {2!r}; "
                "no change was sent".format(nvpair, out[nvpair], profile_key)
            )
        out[nvpair] = profile_key
    return out


def gie_guarded_keys():
    """Registry-known keys whose invalid-parent guard is owned by the GENERIC engine
    (mechanism 'passthrough'). Keys with a dedicated compat validate (child_pti, e.g.
    OSPF-MD) keep their own parent/mode validation and are not double-guarded here."""
    return {
        b["profile_key"]
        for b in BINDING_TABLE
        if b.get("mechanism") == GIE_MECH_PASSTHROUGH
    }


def gie_invalid_parent_key(parent_template, profile_keys):
    """First profile key that is a registry-known GENERIC key but has no valid binding for
    `parent_template` (or the parent is unresolved), else None. A wholly-unknown key is not
    reported here so the caller can preserve the legacy discard behavior."""
    guarded = gie_guarded_keys()
    for pk in profile_keys:
        if pk in guarded and (
            parent_template is None or resolve_binding(parent_template, pk) is None
        ):
            return pk
    return None


def _generic_keys(parent_template):
    """Registered profile keys for a parent handled by the GENERIC eth passthrough path
    (mechanism 'passthrough'). child_pti keys (OSPF-MD) are transported via
    gie_contribute_nvpairs on their own path but are not part of the eth generic spec."""
    keys = set()
    for pk in registered_profile_keys(parent_template):
        b = resolve_binding(parent_template, pk)
        if b and b.get("mechanism") == GIE_MECH_PASSTHROUGH:
            keys.add(pk)
    return keys


def gie_extend_prof_spec(prof_spec, parent_template, profile_input):
    """Add a validation spec entry for each registered generic key the caller set EXPLICITLY.

    The validator type comes from the binding metadata (fail closed on unknown). No default is
    added, so an omitted key stays omitted (dropped by validate_list_of_dicts, exactly as
    before the engine). Returns the same (mutated) prof_spec.
    """
    if prof_spec is None:
        return prof_spec
    for pk in sorted(_generic_keys(parent_template)):
        if pk in profile_input and pk not in prof_spec:
            b = resolve_binding(parent_template, pk)
            entry = {"type": gie_validator_type(b["type"])}
            if b.get("valid_values"):
                entry["choices"] = list(b["valid_values"])
            prof_spec[pk] = entry
    return prof_spec


def _to_nvpair_wire(value):
    """Serialize a value to the form the controller stores in an nvPair.

    nvPairs is a STRING-valued map: NDFC returns every one of them as a string, and the parent
    template DSL tests them as strings (``if disableLldp == "true"``). Every pre-existing
    hardcoded emission in the module already does this by hand -- ``str(x).lower()`` for
    ADMIN_STATE, PORTTYPE_FAST_ENABLED, and the rest.

    Sending a native Python bool instead relies on the controller coercing it on ingest, and it
    breaks idempotency outright: the module compares its own ``True`` against the ``"true"`` the
    controller returns, finds a difference, and re-pushes. Measured live -- DISABLE_LLDP never
    converged, reporting changed=True with a deploy on every single run.

    Booleans use the lowercase JSON spelling, NOT Python's ``str(True)`` == ``"True"``. Strings
    pass through untouched so a case-sensitive value (an ACL name) survives exactly, str
    subclasses included.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    return str(value)


def gie_contribute_nvpairs(parent_template, profile_dict, ndfc_version):
    """Compute the parent nvPairs the engine contributes for one interface, keyed by the
    registered binding mechanism. Returns (nvpairs_dict, error_message).

    Only EXPLICIT registered keys are contributed; an omitted key contributes nothing.

    A PASSTHROUGH value is serialized to its nvPair wire form (see ``_to_nvpair_wire``): that
    mechanism writes straight into the payload, so transport is the whole job and the payload has
    to speak the controller's types. A CHILD_PTI value is left native -- that mechanism is the
    OSPF-MD domain, which reconciles through its own dedicated normalizer and whose call site
    already stringifies explicitly.

    A supported version transports the parent nvPair for every mechanism. An explicit key on an
    unsupported/unknown/malformed version fails closed, except for the one exact OSPF-MD
    compatibility binding, which is withheld for its established HAVE reconciliation.
    """
    add = {}
    for pk in sorted(registered_profile_keys(parent_template)):
        if pk not in profile_dict:
            continue  # omitted -> not emitted
        b = resolve_binding(parent_template, pk)
        gie_validate_binding_value(parent_template, pk, profile_dict[pk])
        supported = gie_version_supported(ndfc_version, b["min_ndfc_version"])
        if not supported:
            if (parent_template, b["parent_nvpair"]) == GIE_OSPF_MD_COMPAT_BINDING:
                # Narrow, per-binding exception: withhold and let the OSPF-MD capability/HAVE
                # compat hook reconcile. NOT applied to any other binding.
                continue
            # Default policy (incl. any ordinary passthrough/child_pti binding): fail closed.
            return None, (
                "'{0}' requires NDFC {1} or later; controller reports {2}. "
                "No change was sent.".format(pk, b["min_ndfc_version"], ndfc_version)
            )
        # Supported version: the engine resolves the binding and transports the value, in the
        # nvPair wire form for passthrough and native for child_pti.
        value = profile_dict[pk]
        if b.get("mechanism") == GIE_MECH_PASSTHROUGH:
            value = _to_nvpair_wire(value)
        add[b["parent_nvpair"]] = value
    return add, None


def gie_carry_forward_bindings(parent_template):
    """Registered GENERIC (passthrough) bindings for a parent whose authoritative controller
    value must be PRESERVED when the profile key is omitted from the playbook (omission is not
    a value). Returns a list of {parent_nvpair, profile_key}. The OSPF-MD child_pti binding
    keeps its own dedicated carry-forward and is not returned here.
    """
    out = []
    if not parent_template:
        return out
    for pk in sorted(registered_profile_keys(parent_template)):
        b = resolve_binding(parent_template, pk)
        if b and b.get("mechanism") == GIE_MECH_PASSTHROUGH:
            out.append({"parent_nvpair": b["parent_nvpair"], "profile_key": pk})
    return out


def gie_have_carry_forward_nvpairs(want_nvpairs, have_nvpairs):
    """Same-parent state:merged HAVE carry-forward (drift fix).

    Return an ordered dict {nvpair: have_value} for every nvPair present in authoritative HAVE that
    the builder did NOT emit into ``want_nvpairs``, EXCLUDING NDFC read-only/identity metadata
    (``GIE_READONLY_METADATA_NVPAIRS``) and the OSPF-MD feature domain
    (``GIE_OSPF_MD_DOMAIN_NVPAIRS``).

    The CALLER restricts this to the exact proven parent (``int_fabric_loopback_11_1``); the exclusion
    set is only demonstrated complete for that parent.

    Fail-closed: a ``have_nvpairs`` that is not a dict (None, list, str, or any malformed value)
    yields ``{}`` -- nothing is carried and nothing is invented. The carried value is the EXACT
    current HAVE value NDFC returned in its GET (a round-trip "leave as-is" assertion, never a default
    or guess), so it cannot introduce a wrong value. A key already present in ``want_nvpairs``
    (explicit user field or a builder-emitted value) is never touched, so explicit/builder always win.
    The caller adds the result to the sent payload only (not to the public diff), keeping the
    user-facing diff and idempotency intact.

    A1.7 note: this is the ONLY carry-forward that runs for ``int_fabric_loopback_11_1``. The
    registered-binding carry-forward (``gie_carry_forward_bindings``) returns [] for that parent
    because it has no ``passthrough`` binding, so the two paths cannot both write the same nvPair.
    The ``nvpair in want_nvpairs`` skip above is the second, independent guarantee of that.
    """
    if not isinstance(have_nvpairs, dict):
        return {}
    out = {}
    for nvpair, value in have_nvpairs.items():
        if nvpair in want_nvpairs:
            continue
        if nvpair in GIE_READONLY_METADATA_NVPAIRS or nvpair in GIE_OSPF_MD_DOMAIN_NVPAIRS:
            continue
        out[nvpair] = value
    return out
