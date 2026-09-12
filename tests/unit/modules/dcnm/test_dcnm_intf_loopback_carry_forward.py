# Actual-comparator-path tests for the same-parent/merged HAVE carry-forward (drift fix).
#
# SCOPE OF THESE TESTS: they construct a DcnmIntf instance and drive the ACTUAL comparator
# `DcnmIntf.dcnm_intf_compare_want_and_have("merged")` directly, asserting its two outputs:
#   * the SENT payload   -> self.diff_replace[0]["interfaces"][0]["nvPairs"]
#   * the PUBLIC diff     -> self.changed_dict[0]["merged"][0]["interfaces"][0]["nvPairs"]
# They do NOT exercise the profile builders, the action plugin, or a full end-to-end module run
# (no AnsibleModule invocation, no live API). Those layers are out of scope here.
#
# Scenario is the confirmed fabric-loopback reproduction: the loopback builder emits a sparse nvPair
# set, so PRIORITY / REPLICATION_MODE / LINK_STATE_ROUTING_TAG / OSPF_AREA_ID live only in HAVE. The
# carry-forward is scoped by the caller to the exact parent int_fabric_loopback_11_1; tests below also
# prove another parent (int_trunk_host) receives NO carry-forward.
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

DcnmIntf = dcnm_interface.DcnmIntf
PARENT = "int_fabric_loopback_11_1"
MD = "ENABLE_OSPF_AUTH_MESSAGE_DIGEST"
SNO = "SN1"
FAB = "fab"

# Builder-emitted nvPairs (present in WANT), matching HAVE so they are idempotent.
BUILDER_NV = {
    "IP": "10.31.0.5",
    "INTF_NAME": "Loopback0",
    "DESC": "Routing loopback interface",
    "CONF": "",
    "ADMIN_STATE": "true",
    "SPEED": "Auto",
    "V6IP": "",
    "ROUTE_MAP_TAG": "",
    "SECONDARY_IP": "",
}
# Writable template nvPairs the builder OMITS -> only in HAVE; these are the ones that drifted live.
HAVE_ONLY_WRITABLE = {
    "PRIORITY": "301",
    "REPLICATION_MODE": "Ingress",
    "LINK_STATE_ROUTING_TAG": "UNDERLAY",
    "OSPF_AREA_ID": "0.0.0.0",
}
# NDFC read-only / identity metadata (must NEVER be carried into the payload).
HAVE_METADATA = {
    "FABRIC_NAME": "FAB1",
    "POLICY_ID": "POLICY-36130",
    "POLICY_DESC": "",
    "MARK_DELETED": "false",
}
# OSPF-MD feature domain (owned by the dedicated path; the generic carry-forward must not touch it).
HAVE_OSPF_DOMAIN = {
    "OSPF_AUTH_KEY": "",
    "OSPF_AUTH_KEY_ID": "",
    "ospfAuthKeychainName": "",
}

# nvPair -> public key map for the comparator (only consulted for keys that differ under merged).
KEYMAP = {
    "IP": "ipv4_addr", "INTF_NAME": "name", "DESC": "description", "CONF": "cmds",
    "ADMIN_STATE": "admin_state", "SPEED": "speed", "V6IP": "ipv6_addr",
    "ROUTE_MAP_TAG": "route_tag", "SECONDARY_IP": "secondary_ipv4_addr",
    "PRIORITY": "priority", "REPLICATION_MODE": "replication_mode",
    "LINK_STATE_ROUTING_TAG": "link_state_routing_tag", "OSPF_AREA_ID": "ospf_area_id",
    MD: "enable_ospf_auth_message_digest",
}


def _instance():
    s = object.__new__(DcnmIntf)  # methods auto-bind from the class; set only data attributes
    s.class_name = "DcnmIntf"
    s.log = mock.Mock()
    s.module = mock.Mock()
    s.fabric = FAB
    s.dcnm_version = 12
    s.pol_pc_member_types = {12: {}}
    s.keymap = dict(KEYMAP)
    s.want_breakout = []
    s.have_breakout = []
    s.have_all = []
    s.intf_detail_cache = {}
    s.intf_detail_cached_snos = set()
    s.intf_detail_fetch_failed_snos = set()
    s.intf_detail_failed_keys = set()
    s.intf_detail_authoritative_absent_keys = set()
    s.have_all_cached_snos = set()
    s.have_all_failed_snos = set()
    s._replace_have_lookup = {}
    s._replace_pb_input_lookup = {}
    s._ospf_auth_md_requests = {}
    s.diff_create = []
    s.diff_replace = []
    s.diff_delete_breakout = []
    s.diff_create_breakout = []
    s.diff_deploy = []
    s.changed_dict = [{
        "merged": [], "replaced": [], "overridden": [], "deleted": [], "query": [],
        "deploy": [], "debugs": [], "delete_deploy": [], "deferred": [], "skipped": [],
    }]
    return s


def _want(nv, policy=PARENT):
    return {
        "policy": policy,
        "interfaceType": "INTERFACE_LOOPBACK",
        "deploy": False,
        "interfaces": [{
            "ifName": "Loopback0", "serialNumber": SNO, "fabricName": FAB,
            "interfaceType": "INTERFACE_LOOPBACK", "nvPairs": dict(nv),
        }],
    }


def _have(nv, policy=PARENT):
    return [{
        "policy": policy,
        "interfaces": [{
            "ifName": "Loopback0", "serialNumber": SNO,
            "interfaceType": "INTERFACE_LOOPBACK", "nvPairs": dict(nv),
        }],
    }]


def _pb(**public_keys):
    item = {"ifname": "Loopback0", "sno": SNO, "fabric": FAB}
    item.update(public_keys)
    return item


def _full_have(md_value):
    nv = {}
    nv.update(BUILDER_NV)
    nv.update(HAVE_ONLY_WRITABLE)
    nv.update(HAVE_METADATA)
    nv.update(HAVE_OSPF_DOMAIN)
    nv[MD] = md_value
    return nv


def _want_md(md_value, extra=None):
    nv = dict(BUILDER_NV)
    nv[MD] = md_value           # engine transports OSPF-MD into want when explicit
    if extra:
        nv.update(extra)
    return nv


def _run(s, state="merged"):
    s.dcnm_intf_compare_want_and_have(state)


def _payload_nv(s):
    if not s.diff_replace:
        return None
    return s.diff_replace[0]["interfaces"][0]["nvPairs"]


def _public_nv(s, state="merged"):
    entries = s.changed_dict[0][state]
    if not entries:
        return None
    return entries[0]["interfaces"][0]["nvPairs"]


# 1. same parent, user changes only OSPF-MD -> full payload preserves the four HAVE nvPairs
def test_payload_preserves_the_four_have_nvpairs():
    s = _instance()
    s.want = [_want(_want_md(True))]
    s.have = _have(_full_have("false"))
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None, "an update payload must be produced"
    for k, v in HAVE_ONLY_WRITABLE.items():
        assert payload.get(k) == v, "carried-forward {0} must equal HAVE".format(k)


# 2. the public diff contains only the user's intent (the Boolean), not the carried keys
def test_public_diff_only_contains_the_boolean():
    s = _instance()
    s.want = [_want(_want_md(True))]
    s.have = _have(_full_have("false"))
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    pub = _public_nv(s)
    assert pub is not None and MD in pub
    for k in list(HAVE_ONLY_WRITABLE) + list(HAVE_METADATA) + list(HAVE_OSPF_DOMAIN):
        assert k not in pub, "{0} must not appear in the public diff".format(k)


# 3. true again (HAVE already true) -> idempotent, no update
def test_true_again_is_idempotent():
    s = _instance()
    s.want = [_want(_want_md(True))]
    s.have = _have(_full_have("true"))
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    assert s.diff_replace == [], "no update expected when OSPF-MD already matches"
    assert s.changed_dict[0]["merged"] == []


# 4. false preserves the four nvPairs; false-again is idempotent
def test_false_preserves_then_idempotent():
    s = _instance()
    s.want = [_want(_want_md(False))]
    s.have = _have(_full_have("true"))
    s.pb_input = [_pb(enable_ospf_auth_message_digest=False)]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    for k, v in HAVE_ONLY_WRITABLE.items():
        assert payload.get(k) == v
    # false again (HAVE already false) -> idempotent
    s2 = _instance()
    s2.want = [_want(_want_md(False))]
    s2.have = _have(_full_have("false"))
    s2.pb_input = [_pb(enable_ospf_auth_message_digest=False)]
    _run(s2)
    assert s2.diff_replace == []


# 5. an explicit user field always wins over HAVE (never overridden by carry-forward)
def test_explicit_user_field_wins_over_have():
    s = _instance()
    # user declares route_tag=999 -> builder emits ROUTE_MAP_TAG=999 into want; HAVE has "100"
    s.want = [_want(_want_md(True, extra={"ROUTE_MAP_TAG": "999"}))]
    have_nv = _full_have("false")
    have_nv["ROUTE_MAP_TAG"] = "100"
    s.have = _have(have_nv)
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True, route_tag="999")]
    _run(s)
    payload = _payload_nv(s)
    assert payload.get("ROUTE_MAP_TAG") == "999", "explicit user value must win, not HAVE 100"
    assert _public_nv(s).get("ROUTE_MAP_TAG") == "999"


# 6. NDFC read-only / identity metadata is NEVER carried into the payload
def test_metadata_identity_never_carried():
    s = _instance()
    s.want = [_want(_want_md(True))]
    s.have = _have(_full_have("false"))
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    payload = _payload_nv(s)
    for k in ("FABRIC_NAME", "POLICY_ID", "POLICY_DESC", "MARK_DELETED"):
        assert k not in payload, "read-only metadata {0} must never be carried".format(k)


# 7. the OSPF-MD sensitive domain is NEVER carried by the generic carry-forward
def test_ospf_domain_never_carried():
    s = _instance()
    # HAVE carries key material; the generic carry-forward must not echo it back
    have_nv = _full_have("false")
    have_nv["OSPF_AUTH_KEY"] = "somecipher"
    have_nv["OSPF_AUTH_KEY_ID"] = "3"
    have_nv["ospfAuthKeychainName"] = "KC1"
    s.want = [_want(_want_md(True))]
    s.have = _have(have_nv)
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    payload = _payload_nv(s)
    for k in ("OSPF_AUTH_KEY", "OSPF_AUTH_KEY_ID", "ospfAuthKeychainName"):
        assert k not in payload, "OSPF domain {0} must not be carried by the generic path".format(k)


# 8a. a parent/policy change gets NO carry-forward (mismatch path continues before the block)
def test_parent_change_no_carry_forward():
    s = _instance()
    s.want = [_want(_want_md(True), policy="int_loopback")]      # desired parent differs
    s.have = _have(_full_have("false"), policy=PARENT)           # current parent is fabric loopback
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None, "policy change still produces an update payload"
    for k in HAVE_ONLY_WRITABLE:
        assert k not in payload, "no cross-parent carry-forward of {0}".format(k)


# 8b. authoritative absent HAVE -> existing contract adds; the carry-forward invents nothing.
def test_absent_have_is_add_not_carry_forward():
    s = _instance()
    s.want = [_want(_want_md(True))]
    s.have = []  # authoritative absence -> existing 'add' path, no match_have
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)  # must not raise
    assert s.diff_replace == [], "absent HAVE is an add, not a replace"
    added = s.diff_create[0]["interfaces"][0]["nvPairs"] if s.diff_create else {}
    for k in HAVE_ONLY_WRITABLE:
        assert k not in added, "nothing invented when there is no HAVE to carry"


# 8c. the carry-forward helper is fail-safe for missing/empty HAVE and honors the exclusions,
#     so a malformed/empty HAVE never invents values and never transports metadata / OSPF domain.
def test_carry_forward_helper_fail_safe_and_exclusions():
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
        gie_have_carry_forward_nvpairs,
    )
    assert gie_have_carry_forward_nvpairs({"IP": "x"}, None) == {}
    assert gie_have_carry_forward_nvpairs({"IP": "x"}, {}) == {}
    # want-present keys are never overridden; metadata + OSPF domain are never carried;
    # only the builder-omitted writable nvPair is carried.
    have = {"IP": "keep", "PRIORITY": "301", "POLICY_ID": "p", "FABRIC_NAME": "f",
            "OSPF_AUTH_KEY": "k", "ENABLE_OSPF_AUTH_MESSAGE_DIGEST": "true"}
    assert gie_have_carry_forward_nvpairs({"IP": "x"}, have) == {"PRIORITY": "301"}
    # fail-closed for any non-dict HAVE (not only None/{}): list, str, int -> {}
    for bad in ([], ["x"], "notadict", 123, ("t",)):
        assert gie_have_carry_forward_nvpairs({}, bad) == {}, "non-dict HAVE must yield {{}}"


# BLOCKER-1 scope: the carry-forward is restricted by the caller to the exact proven parent.
# 9. another parent with a builder-omitted HAVE-only nvPair gets NO carry-forward
def test_other_parent_no_carry_forward():
    s = _instance()
    want_nv = dict(BUILDER_NV)
    want_nv["DESC"] = "changed"                       # a declared change -> action=update
    s.want = [_want(want_nv, policy="int_trunk_host")]
    have_nv = dict(BUILDER_NV)
    have_nv["DESC"] = "orig"
    have_nv["SOME_WRITABLE_NVP"] = "keepme"           # HAVE-only writable on a non-OSPF parent
    s.have = _have(have_nv, policy="int_trunk_host")
    s.keymap["SOME_WRITABLE_NVP"] = "some_writable"
    s.pb_input = [_pb(description="changed")]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    assert "SOME_WRITABLE_NVP" not in payload, "no carry-forward for a non-OSPF parent"


# 10. the SAME nvPair name on another parent also does NOT activate the behavior (parent-scoped)
def test_same_nvpair_name_other_parent_no_carry_forward():
    s = _instance()
    want_nv = dict(BUILDER_NV)
    want_nv["DESC"] = "changed"
    s.want = [_want(want_nv, policy="int_trunk_host")]
    have_nv = dict(BUILDER_NV)
    have_nv["DESC"] = "orig"
    have_nv["PRIORITY"] = "301"                        # same name as a fabric-loopback drift key
    s.have = _have(have_nv, policy="int_trunk_host")
    s.pb_input = [_pb(description="changed")]
    _run(s)
    payload = _payload_nv(s)
    assert "PRIORITY" not in payload, "same nvPair name on another parent must not be carried"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
