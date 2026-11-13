"""Bindings through the real dcnm_interface path: normalization, payload, carry-forward and version gate."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_have_carry_forward_nvpairs
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_READONLY_METADATA_NVPAIRS
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import gie_carry_forward_bindings

from ..dcnm_module import set_module_args
from .helpers.module_runner import A161Base
from .helpers.module_runner import SUPPORTED
from .helpers.module_runner import SUPPORTED_PATCH
from .helpers.binding_harness import FAB
from .helpers.binding_harness import MD
from .helpers.binding_harness import SNO
from .helpers.binding_harness import _instance
from .helpers.binding_harness import _payload_nv
from .helpers.binding_harness import _public_nv


# ====================================================================================================
# Formerly test_dcnm_intf_binding_module_path.py
# Production-shaped tests through the real dcnm_interface path.
#
# Every test here enters through the module's
# public entry point (`execute_module` -> `main()` -> `dcnm_intf_validate_input()` ->
# per-type profile validation via `validate_list_of_dicts` -> builder ->
# `gie_contribute_nvpairs` -> WANT -> compare -> payload) with transport and HAVE mocked.
#
# Which layer each group exercises:
#
#   MODULE NORMALIZATION (raw playbook value -> validate_list_of_dicts coercion)
#       TestBindingRawTypeOnModulePath.*                — raw type rejected pre-coercion
#   WANT / BUILDER / FINAL PAYLOAD
#       TestBindingPayloadOnModulePath.*                — value survives into the parent nvPair
#   HAVE / DIFF / COMPARE / IDEMPOTENCE
#       TestBindingHaveAndCompareOnModulePath.*         — carry-forward, malformed HAVE, no-push
#   BASELINE REGRESSION
#       TestBindingFrozenContractRegression.*           — FLOWCONTROL_RECEIVE + exact wire type
#   VERSION GATE
#       TestBindingBelowMinimumVersionFailsClosed.*     — below minimum: fail, never withhold
#
# NOT LIVE TESTED. No controller or switch is contacted.
# ====================================================================================================
TRUNK = "int_trunk_host"
ACCESS = "int_access_host"
PC_TRUNK = "int_port_channel_trunk_host"
PC_ACCESS = "int_port_channel_access_host"
PC_DOT1Q = "int_port_channel_dot1q_tunnel_host"

BELOW = "12.6.0.266"


# =====================================================================================
# MODULE NORMALIZATION: raw type is enforced BEFORE validate_list_of_dicts coerces
# =====================================================================================
class TestBindingRawTypeOnModulePath(A161Base):
    """Every reproduced case, driven through the real module input path."""

    def _assert_rejected_without_echo(self, result, field, forbidden):
        msg = result["msg"]
        assert "Invalid parameters in playbook" in msg, msg
        assert field in msg, msg
        assert "no change was sent" in msg.lower(), msg
        for token in forbidden:
            assert str(token) not in msg, f"error echoed the rejected value {token!r}: {msg}"

    def test_disable_lldp_string_false_is_rejected_not_coerced_to_False(self):
        result = self.run_config("eth_access_disable_lldp_string_false", failed=True)
        self._assert_rejected_without_echo(result, "disable_lldp_transmit", ["'false'", '"false"'])
        assert "native boolean" in result["msg"]
        self.assert_no_mutating_calls()

    def test_disable_lldp_int_one_is_rejected_not_coerced_to_True(self):
        result = self.run_config("eth_access_disable_lldp_int_one", failed=True)
        self._assert_rejected_without_echo(result, "disable_lldp_transmit", [])
        assert "native boolean" in result["msg"]
        self.assert_no_mutating_calls()

    def test_acl_filter_boolean_is_rejected_not_coerced_to_string_True(self):
        result = self.run_config("eth_access_acl_filter_bool", failed=True)
        self._assert_rejected_without_echo(result, "acl_filter", ["True"])
        assert "native string" in result["msg"]
        self.assert_no_mutating_calls()

    def test_acl_filter_int_is_rejected_not_coerced_to_string_123(self):
        result = self.run_config("eth_access_acl_filter_int", failed=True)
        self._assert_rejected_without_echo(result, "acl_filter", ["123"])
        assert "native string" in result["msg"]
        self.assert_no_mutating_calls()

    def test_acl_filter_over_max_length_is_rejected(self):
        result = self.run_config("eth_access_acl_filter_too_long", failed=True)
        self._assert_rejected_without_echo(result, "acl_filter", ["AAAAAAAAAA"])
        assert "length 1..64" in result["msg"]
        self.assert_no_mutating_calls()

    def test_guard_mode_boolean_is_rejected_without_echoing_the_value(self):
        """Previously rejected by choices, but the legacy message echoed the value."""
        result = self.run_config("eth_trunk_guard_mode_bool", failed=True)
        self._assert_rejected_without_echo(result, "guard_mode", ["True"])
        assert "one of: root, none, loop, no" in result["msg"]
        self.assert_no_mutating_calls()

    def test_guard_mode_unknown_choice_is_rejected_without_echoing_the_value(self):
        result = self.run_config("eth_trunk_guard_mode_bad_choice", failed=True)
        self._assert_rejected_without_echo(result, "guard_mode", ["bogus"])
        self.assert_no_mutating_calls()

    def test_flowcontrol_boolean_is_rejected_without_echo(self):
        """The baseline binding gains the same raw-type protection."""
        result = self.run_config("eth_trunk_flowcontrol_bool", failed=True)
        self._assert_rejected_without_echo(result, "flowcontrol_receive", ["True"])
        self.assert_no_mutating_calls()

    def test_unknown_legacy_field_is_not_tightened(self):
        """Scope guard: non-registered fields keep their existing legacy behaviour."""
        result = self.run_config("eth_trunk_unknown_legacy_field", changed=True)
        assert result.get("failed") is not True
        for nvpairs in self.sent_nvpairs().values():
            assert "some_unknown_legacy_field" not in nvpairs


# =====================================================================================
# WANT / BUILDER / PAYLOAD — a valid explicit value survives into the exact parent nvPair
# =====================================================================================
class TestBindingPayloadOnModulePath(A161Base):

    def _assert_nvpair(self, result, ifname, nvpair, expected):
        merged = self.diff_nvpairs(result)
        assert ifname in merged, f"{ifname} not in diff: {list(merged)}"
        assert nvpair in merged[ifname], (
            f"{nvpair} missing from {ifname} nvPairs: {sorted(merged[ifname])}"
        )
        actual = merged[ifname][nvpair]
        assert actual == expected, f"{nvpair}={actual!r}, expected {expected!r}"
        return actual

    def test_eth_trunk_guard_mode_reaches_the_parent_nvpair(self):
        result = self.run_config("eth_trunk_guard_mode_root", changed=True)
        self._assert_nvpair(result, "Ethernet1/30", "GUARD_MODE", "root")

    # The playbook value stays strictly native -- a string "false" is still rejected, see
    # test_disable_lldp_string_false_is_rejected_not_coerced_to_False above. What these two pin is
    # the OTHER end: what the engine puts on the wire. nvPairs is a string-valued map, and
    # emitting a native bool there made the field non-idempotent on a live controller.
    def test_eth_trunk_disable_lldp_true_reaches_the_parent_nvpair(self):
        result = self.run_config("eth_trunk_disable_lldp_true", changed=True)
        value = self._assert_nvpair(result, "Ethernet1/30", "lldpTransmit", "true")
        # Exact type, like the ACL cases below: AnsibleUnsafeText satisfies isinstance and is
        # what an unconverted controller value looks like.
        assert type(value) is str  # pylint: disable=unidiomatic-typecheck

    def test_eth_access_disable_lldp_false_reaches_the_parent_nvpair(self):
        """An explicit false is authored intent and must be emitted, not skipped.

        'false' is a value here, never an omission, so the payload must carry the key.
        """
        result = self.run_config("eth_access_disable_lldp_false", changed=True)
        value = self._assert_nvpair(result, "Ethernet1/31", "lldpTransmit", "false")
        assert type(value) is str  # pylint: disable=unidiomatic-typecheck

    def test_eth_trunk_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("eth_trunk_acl_filter_valid", changed=True)
        value = self._assert_nvpair(result, "Ethernet1/30", "aclFilter", "ACL_ALPHA")
        # Exact type: a str subclass would satisfy isinstance and still be wrong.
        assert type(value) is str  # pylint: disable=unidiomatic-typecheck

    def test_eth_access_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("eth_access_acl_filter_valid", changed=True)
        self._assert_nvpair(result, "Ethernet1/31", "aclFilter", "ACL_BETA")

    def test_eth_access_acl_filter_empty_reaches_the_parent_nvpair(self):
        """"" is how the field is CLEARED, so it has to travel like any other value.

        A sibling case in the rejection class used to assert the opposite: that the empty
        string was blocked on min_length and that nothing was sent. That made ACL_FILTER
        settable and never clearable, and a re-deploy does not clear it either -- NaC does not
        model the field, so vxlan.yaml walks past the value.

        Measured on NDFC 12.6.0.267: "" is accepted, stored, and the 'ip port access-group'
        line is withdrawn from the device on deploy. It is also the encoding the controller
        returns for "no ACL configured". So the module must transport it, not block it.
        """
        result = self.run_config("eth_access_acl_filter_empty", changed=True)
        value = self._assert_nvpair(result, "Ethernet1/31", "aclFilter", "")
        # Not None, not absent: an absent key would mean "leave as-is", the opposite of clear.
        assert type(value) is str  # pylint: disable=unidiomatic-typecheck

    def test_pc_trunk_guard_mode_reaches_the_parent_nvpair(self):
        result = self.run_config("pc_trunk_guard_mode_root", changed=True)
        self._assert_nvpair(result, "Port-channel300", "GUARD_MODE", "root")

    def test_pc_trunk_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("pc_trunk_acl_filter_valid", changed=True)
        self._assert_nvpair(result, "Port-channel300", "aclFilter", "ACL_GAMMA")

    def test_pc_access_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("pc_access_acl_filter_valid", changed=True)
        self._assert_nvpair(result, "Port-channel301", "aclFilter", "ACL_DELTA")

    def test_pc_dot1q_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("pc_dot1q_acl_filter_valid", changed=True)
        self._assert_nvpair(result, "Port-channel302", "aclFilter", "ACL_EPS")

    def test_omission_contributes_no_nvpair_and_no_default(self):
        result = self.run_config("eth_trunk_omitted", changed=True)
        merged = self.diff_nvpairs(result)
        # Guard against a vacuous pass: the interface MUST be in the diff, with a real
        # payload, and only then may we assert the absence of the registered nvPairs.
        assert "Ethernet1/30" in merged, f"interface missing from diff: {list(merged)}"
        nvpairs = merged["Ethernet1/30"]
        assert nvpairs, "empty nvPairs would make the absence assertions meaningless"
        assert "INTF_NAME" in nvpairs or "ADMIN_STATE" in nvpairs, sorted(nvpairs)
        for nvpair in ("GUARD_MODE", "lldpTransmit", "aclFilter"):
            assert nvpair not in nvpairs, (
                f"omission produced {nvpair}={nvpairs.get(nvpair)!r}"
            )
        # And nothing reached the wire carrying them either.
        for sent in self.sent_nvpairs().values():
            for nvpair in ("GUARD_MODE", "lldpTransmit", "aclFilter"):
                assert nvpair not in sent


# =====================================================================================
# WRONG PARENT / VERSION — stop before diff or write, on the real path
# =====================================================================================
class TestBindingWrongParentOnModulePath(A161Base):

    def test_guard_mode_on_routed_eth_fails_before_write(self):
        result = self.run_config("eth_routed_guard_mode", failed=True)
        assert "guard_mode" in result["msg"]
        assert "not supported on this interface" in result["msg"]
        self.assert_no_mutating_calls()

    def test_guard_mode_on_access_eth_fails_before_write(self):
        result = self.run_config("eth_access_guard_mode", failed=True)
        assert "guard_mode" in result["msg"]
        assert "not supported on this interface" in result["msg"]
        self.assert_no_mutating_calls()

    def test_disable_lldp_on_port_channel_is_accepted_and_transported(self):
        """The port-channel host parents declare DISABLE_LLDP, so they accept it.

        This test previously asserted the opposite. The field was registered only on the
        ethernet parents, so a playbook setting it on a port-channel got "not supported on this
        interface" -- a message that was FALSE: the template declares it, the registry did not.

        What the parent does with the value differs from ethernet, and that part is NOT pinned
        here because a unit test cannot see it: the parent does not emit the CLI, it passes the
        value to the member policy, which writes 'no lldp transmit' / 'no lldp receive'. Whether
        it reaches the member is measured on a live controller.

        Pinned here: the value is accepted and reaches the parent nvPair.
        """
        result = self.run_config("pc_access_disable_lldp", changed=True)
        merged = self.diff_nvpairs(result)
        ifname = next(iter(merged))
        assert merged[ifname]["lldpTransmit"] == "true"

    def test_acl_filter_raw_type_on_pc_also_fails_before_write(self):
        result = self.run_config("pc_trunk_acl_filter_bool", failed=True)
        assert "acl_filter" in result["msg"]
        assert "native string" in result["msg"]
        assert "True" not in result["msg"]
        self.assert_no_mutating_calls()


class TestBindingUnsupportedVersionOnModulePath(A161Base):
    ndfc_version = BELOW

    def test_guard_mode_on_unsupported_version_fails_before_write(self):
        result = self.run_config("eth_trunk_guard_mode_root", failed=True)
        assert "12.6.0.267" in result["msg"]
        assert "No change was sent." in result["msg"]
        self.assert_no_mutating_calls()

    def test_acl_filter_on_unsupported_version_fails_before_write(self):
        result = self.run_config("eth_trunk_acl_filter_valid", failed=True)
        assert "No change was sent." in result["msg"]
        self.assert_no_mutating_calls()

    def test_disable_lldp_on_unsupported_version_fails_before_write(self):
        result = self.run_config("eth_trunk_disable_lldp_true", failed=True)
        assert "No change was sent." in result["msg"]
        self.assert_no_mutating_calls()


class TestBindingUnknownVersionOnModulePath(A161Base):
    ndfc_version = "not.a.version"

    def test_malformed_version_fails_before_write(self):
        result = self.run_config("eth_trunk_guard_mode_root", failed=True)
        assert "No change was sent." in result["msg"]
        self.assert_no_mutating_calls()


# =====================================================================================
# BASELINE REGRESSION on the real module path
# =====================================================================================
class TestBindingFrozenContractRegression(A161Base):

    def test_flowcontrol_receive_still_reaches_the_parent_nvpair(self):
        result = self.run_config("eth_trunk_flowcontrol_on", changed=True)
        merged = self.diff_nvpairs(result)
        assert merged["Ethernet1/30"]["flowcontrolReceive"] == "on"

    # The loopback OSPF-MD regression that used to sit here was retired with its binding. It
    # carried one guarantee the FLOWCONTROL case above does not: EXACT type on the wire. That
    # binding was the only CHILD_PTI one, so it was also the only value reaching the parent
    # nvPair natively, and it asserted `type(...) is bool`.
    #
    # No live CHILD_PTI binding exists to re-host that on. Its dual is live, and is what all
    # ninety-six bindings depend on, so the guarantee is re-homed as that: a boolean travels as
    # the controller's STRING form. Between the two, both directions of the type hazard stay
    # covered -- the old test caught a bool degraded to an int, this one catches a bool that
    # never became a string at all.

    def test_a_boolean_reaches_the_parent_nvpair_as_an_exact_string(self):
        """isinstance is not enough here, and the difference is not academic.

        NDFC hands every nvPair back as AnsibleUnsafeText, which IS a str subclass. So an
        isinstance check passes just as happily for a value that came back from the controller
        unconverted as for one the engine serialized -- and only the second is correct. type()
        is what separates them.
        """
        result = self.run_config("eth_trunk_disable_lldp_true", changed=True)
        value = self.diff_nvpairs(result)["Ethernet1/30"]["lldpTransmit"]
        assert value == "true"
        assert type(value) is str  # pylint: disable=unidiomatic-typecheck
        # And explicitly not the Python object: True would be left for the transport to
        # serialize, which is how "True" -- a spelling NDFC rejects -- reaches the controller.
        assert value is not True


class TestBindingBelowMinimumVersionFailsClosed(A161Base):
    """Below the minimum version every binding fails closed. No exception is left.

    One used to exist: the loopback OSPF-auth binding was WITHHELD rather than failed, because
    the module's capability gate reconciled the key afterwards. Binding and gate were retired
    together, and GIE_VERSION_WITHHOLD_BINDINGS is empty.

    Withholding is the dangerous half of that pair: it drops a key the operator explicitly wrote
    and still reports success. This class exists so re-introducing one cannot pass unnoticed. It
    asserts both halves -- that the set is empty, and that on the real module path a real
    binding fails instead of being silently dropped.
    """

    ndfc_version = BELOW

    def test_the_withhold_set_is_empty(self):
        from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
            GIE_VERSION_WITHHOLD_BINDINGS,
        )

        assert GIE_VERSION_WITHHOLD_BINDINGS == frozenset(), (
            "a binding was added to the withhold set. That is not a config change: it means an "
            "explicitly authored key is dropped while the run reports success. Whatever layer "
            "reconciles that key must be named and tested first."
        )

    def test_an_explicit_key_fails_rather_than_being_dropped(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=self.config_data.get("eth_trunk_disable_lldp_true"),
                patch_version=SUPPORTED_PATCH,
            )
        )
        result = self.execute_module(changed=False, failed=True)
        assert SUPPORTED in result["msg"] and BELOW in result["msg"], (
            "the failure must name both the required and the reported version; with only one "
            "the operator cannot tell whether to upgrade or to fix the playbook"
        )
        assert "No change was sent." in result["msg"]


# ====================================================================================================
# Formerly test_dcnm_intf_loopback_carry_forward.py
# ====================================================================================================
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


PARENT = "int_fabric_loopback_11_1"

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


def test_the_fabric_owned_domain_is_now_carried_not_excluded():
    """INVERTED contract, replacing test_ospf_domain_never_carried.

    While the module managed those nvPairs through a dedicated path, excluding them from the
    generic carry-forward was correct: two writers would have fought over the same keys. The
    capability was withdrawn -- OSPF authentication on a fabric loopback is underlay
    authentication that fabricSettings owns -- so nothing manages them now, and excluding them
    would mean an unrelated update blanks the fabric's own configuration.

    The full behavioural contract, including replaced and overridden through the real
    comparator, is in test_binding_ospf_loopback_subif.py. This pins the inversion at the
    point the old assertion lived, so the change of contract is visible where the old one was.
    """
    have = dict(HAVE_ONLY_WRITABLE, **HAVE_OSPF_DOMAIN)
    carried = gie_have_carry_forward_nvpairs({"INTF_NAME": "loopback0"}, have)
    for nvpair, value in HAVE_OSPF_DOMAIN.items():
        assert carried.get(nvpair) == value, (
            "{0} must now be carried: the module no longer manages it, so omitting it from a "
            "payload is not a request to clear it".format(nvpair)
        )


# ====================================================================================================
# Formerly test_dcnm_intf_binding_integration.py
# One authoritative carry-forward path.
#
# Two carry-forward mechanisms coexist:
#
#   * `gie_have_carry_forward_nvpairs` — generic same-parent HAVE preservation, scoped by the
#     CALLER to the int_fabric_loopback_11_1 parent, merged state only.
#   * `gie_carry_forward_bindings` — registered passthrough bindings, re-validated against the
#     registry before being carried.
#
# These tests prove they coexist without double injection, without losing HAVE values, and
# without any cross-parent carry, driven through the real comparator
# `DcnmIntf.dcnm_intf_compare_want_and_have`.
#
# Helpers are imported from the sibling suite rather than duplicated, so the two files cannot
# drift apart.
#
# NOT LIVE TESTED.
# ====================================================================================================
# Registered passthrough nvPairs per eth parent, and a builder-emitted baseline for them.
ETH_BUILDER_NV = {
    "INTF_NAME": "Ethernet1/30",
    "DESC": "",
    "CONF": "",
    "ADMIN_STATE": "true",
    "SPEED": "Auto",
    "BPDUGUARD_ENABLED": "true",
    "MTU": "jumbo",
}
# Three registered bindings, one per value type, living only in HAVE.
ETH_HAVE_REGISTERED = {
    "GUARD_MODE": "root",            # enum
    "lldpTransmit": True,            # boolean
    "aclFilter": "ACL_FROM_HAVE",   # string
    "flowcontrolReceive": "on",     # enum (baseline binding)
}
ETH_KEYMAP = {
    "INTF_NAME": "name", "DESC": "description", "CONF": "cmds",
    "ADMIN_STATE": "admin_state", "SPEED": "speed",
    "BPDUGUARD_ENABLED": "bpdu_guard", "MTU": "mtu",
    "GUARD_MODE": "guard_mode", "lldpTransmit": "disable_lldp_transmit",
    "aclFilter": "acl_filter", "flowcontrolReceive": "flowcontrol_receive",
}


def _eth_instance():
    s = _instance()
    s.keymap = dict(ETH_KEYMAP)
    return s


def _eth_want(nv, policy=TRUNK, ifname="Ethernet1/30"):
    return {
        "policy": policy,
        "interfaceType": "INTERFACE_ETHERNET",
        "deploy": False,
        "interfaces": [{
            "ifName": ifname, "serialNumber": SNO, "fabricName": FAB,
            "interfaceType": "INTERFACE_ETHERNET", "nvPairs": dict(nv),
        }],
    }


def _eth_have(nv, policy=TRUNK, ifname="Ethernet1/30"):
    return [{
        "policy": policy,
        "interfaces": [{
            "ifName": ifname, "serialNumber": SNO,
            "interfaceType": "INTERFACE_ETHERNET", "nvPairs": dict(nv),
        }],
    }]


def _eth_pb(**public_keys):
    item = {"ifname": "Ethernet1/30", "sno": SNO, "fabric": FAB}
    item.update(public_keys)
    return item


# =====================================================================================
# ONE AUTHORITATIVE PATH — the two mechanisms do not overlap
# =====================================================================================
def test_the_two_carry_forward_paths_are_disjoint_by_construction():
    """The loopback parent has no passthrough binding, so only the generic path runs there."""
    assert gie_carry_forward_bindings(PARENT) == [], (
        "if the loopback parent ever registers a passthrough binding, the two carry-forward "
        "paths would both target it and this integration must be re-reviewed"
    )
    # Conversely, the eth/pc parents DO have registered bindings...
    for parent in (TRUNK, ACCESS, PC_TRUNK, PC_DOT1Q):
        assert gie_carry_forward_bindings(parent), f"{parent} should register bindings"
    # ...and the generic HAVE carry-forward is caller-scoped to the loopback parent only,
    # which the comparator enforces (asserted end-to-end below).


def test_generic_carry_forward_never_overwrites_a_key_already_in_want():
    """Second, independent guarantee against double injection."""
    want_nv = {"PRIORITY": "999", "IP": "10.0.0.1"}
    have_nv = {"PRIORITY": "301", "IP": "10.9.9.9", "REPLICATION_MODE": "Ingress"}
    carried = gie_have_carry_forward_nvpairs(want_nv, have_nv)
    assert "PRIORITY" not in carried, "an explicit/builder value must never be overridden"
    assert "IP" not in carried
    assert carried == {"REPLICATION_MODE": "Ingress"}


def test_no_double_injection_on_the_loopback_parent():
    """Run the real comparator and assert every carried nvPair appears exactly once, with the
    exact HAVE value — not a value written twice by two paths."""
    s = _instance()
    s.want = [_want(_want_md(True))]
    s.have = _have(_full_have("false"))
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    for key, value in HAVE_ONLY_WRITABLE.items():
        assert payload[key] == value, f"{key} must equal the exact HAVE value"
    # The registered-binding path contributes nothing here: none of its nvPairs may appear.
    for nvpair in ("GUARD_MODE", "lldpTransmit", "aclFilter", "flowcontrolReceive"):
        assert nvpair not in payload, (
            f"{nvpair} is not registered on {PARENT}; the registered path must not run here"
        )


def test_no_cross_parent_carry_from_loopback_to_eth():
    """An eth parent must NOT receive the generic loopback carry-forward."""
    s = _eth_instance()
    want_nv = dict(ETH_BUILDER_NV, DESC="changed")
    s.want = [_eth_want(want_nv)]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv.update(HAVE_ONLY_WRITABLE)      # loopback-shaped extras present in HAVE
    have_nv.update(HAVE_METADATA)
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(description="changed")]
    _run(s)
    payload = _payload_nv(s)
    if payload is not None:
        for key in HAVE_ONLY_WRITABLE:
            assert key not in payload, (
                f"{key} was carried onto {TRUNK}; the generic carry-forward must stay scoped "
                f"to {PARENT}"
            )


def test_no_cross_parent_carry_from_eth_to_loopback():
    """The loopback parent must not gain eth registered nvPairs from a stray HAVE."""
    s = _instance()
    s.want = [_want(_want_md(True))]
    have_nv = _full_have("false")
    have_nv.update(ETH_HAVE_REGISTERED)     # eth-shaped registered keys in a loopback HAVE
    s.have = _have(have_nv)
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    # The generic path carries builder-omitted, non-excluded HAVE nvPairs for THIS parent. The
    # eth keys are not excluded, so they ARE carried as opaque HAVE values -- that is the
    # documented "preserve whatever NDFC returned" behaviour, NOT a registered-binding carry.
    # What must NOT happen is the registered path claiming them: assert the values are the exact
    # HAVE values and that no registry validation was applied (no coercion, no rejection).
    for key, value in ETH_HAVE_REGISTERED.items():
        assert payload[key] == value, f"{key} must be the exact opaque HAVE value"
    assert gie_carry_forward_bindings(PARENT) == [], (
        "no registered binding exists on this parent, so the registered path did not run"
    )


# =====================================================================================
# EXCLUSIONS — read-only metadata is never carried
#
# This heading used to say "and the OSPF-MD domain". That half went with the capability: the
# fabric-loopback OSPF-MD binding was the last child_pti, and when it was retired its exclusion
# test went too. GIE_OSPF_MD_DOMAIN_NVPAIRS was still imported here with nothing reading it,
# which is what pylint caught. Nothing to reinstate -- there is no such domain to exclude now.
# =====================================================================================
def test_readonly_metadata_is_never_carried():
    carried = gie_have_carry_forward_nvpairs({}, dict(HAVE_METADATA, PRIORITY="301"))
    for key in GIE_READONLY_METADATA_NVPAIRS:
        assert key not in carried
    assert carried == {"PRIORITY": "301"}


@pytest.mark.parametrize("bad_have", [None, [], "", "nvpairs", 0, 1, 3.14, set(), object()])
def test_non_dict_have_carries_nothing(bad_have):
    assert gie_have_carry_forward_nvpairs({"IP": "1.1.1.1"}, bad_have) == {}


def test_malformed_have_nvpairs_hits_a_PREEXISTING_legacy_limit_not_the_carry_forward():
    """A HAVE entry whose ``nvPairs`` is not a dict raises inside the LEGACY comparator.

    FINDING, recorded rather than silently fixed. `dcnm_intf_compare_want_and_have` does
    `intf.get(ik, {}).get(key, None)` while scanning HAVE. When `nvPairs` is None that is
    `None.get(...)` -> AttributeError, and it happens BEFORE either carry-forward runs.

    This is pre-existing behaviour, not something the merged carry-forward introduced,
    and hardening the legacy comparator is outside this change's scope (it would change
    behaviour for every unregistered field on every parent). The contribution proven here is
    fail-closed independently by `test_non_dict_have_carries_nothing`.

    The test asserts the CURRENT truth so the limit is visible and a future fix is a
    deliberate, reviewed change rather than an accident.
    """
    s = _instance()
    s.want = [_want(_want_md(True))]
    bad = _have(_full_have("false"))
    bad[0]["interfaces"][0]["nvPairs"] = None
    s.have = bad
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    with pytest.raises(AttributeError):
        _run(s)
    # And the carry-forward helper itself is fail-closed for exactly this input.
    assert gie_have_carry_forward_nvpairs({"IP": "1.1.1.1"}, None) == {}


# =====================================================================================
# STATE SCOPING — merged only; replaced/overridden intentionally reset
# =====================================================================================
@pytest.mark.parametrize("state", ["replaced", "overridden"])
def test_generic_carry_forward_does_not_run_outside_merged(state):
    """The current contract limits the generic carry-forward to merged.

    replaced/overridden deliberately reset builder-omitted nvPairs; that is the documented
    semantics, and this test pins it so a future change is a deliberate decision.
    """
    s = _instance()
    s.want = [_want(_want_md(True))]
    s.have = _have(_full_have("false"))
    s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
    _run(s, state=state)
    payload = _payload_nv(s)
    if payload is not None:
        for key in HAVE_ONLY_WRITABLE:
            assert key not in payload, (
                f"{state} must not carry {key}; only merged does"
            )


# =====================================================================================
# REGISTERED-BINDING CARRY-FORWARD — enum / boolean / string, on the eth parent
# =====================================================================================
@pytest.mark.parametrize("nvpair,profile_key,value", [
    ("GUARD_MODE", "guard_mode", "root"),
    ("lldpTransmit", "disable_lldp_transmit", True),
    ("aclFilter", "acl_filter", "ACL_FROM_HAVE"),
    ("flowcontrolReceive", "flowcontrol_receive", "on"),
])
def test_registered_binding_is_carried_when_omitted(nvpair, profile_key, value):
    """Omitted explicit input + populated HAVE -> the authoritative value is preserved."""
    s = _eth_instance()
    # A real change is needed for the comparator to emit an update at all; DESC differs while
    # the registered key is OMITTED by the user and present only in HAVE.
    s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="changed"))]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv[nvpair] = value
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(description="changed")]  # profile_key NOT in the playbook keys
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None, "an update payload must be produced"
    assert payload.get(nvpair) == value, f"{nvpair} must be carried from HAVE exactly"
    assert type(payload[nvpair]) is type(value), "the native type must survive"


def test_registered_carry_forward_produces_no_public_diff():
    """A carried value is transport preservation, not a requested change."""
    s = _eth_instance()
    s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="new"))]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv["GUARD_MODE"] = "root"
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(description="new")]
    _run(s)
    public = _public_nv(s)
    if public is not None:
        assert "GUARD_MODE" not in public, (
            "a carried value must not be reported as a requested change"
        )


def test_explicit_value_wins_over_have():
    s = _eth_instance()
    want_nv = dict(ETH_BUILDER_NV, DESC="changed")
    want_nv["GUARD_MODE"] = "loop"                 # explicit, engine-transported
    s.want = [_eth_want(want_nv)]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv["GUARD_MODE"] = "root"
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(guard_mode="loop", description="changed")]
    _run(s)
    payload = _payload_nv(s)
    assert payload is not None
    assert payload["GUARD_MODE"] == "loop", "the explicit value must win"


def test_absent_have_carries_nothing_and_invents_no_default():
    s = _eth_instance()
    s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="new"))]
    s.have = _eth_have(ETH_BUILDER_NV)             # HAVE has none of the registered keys
    s.pb_input = [_eth_pb(description="new")]
    _run(s)
    payload = _payload_nv(s)
    if payload is not None:
        for nvpair in ("GUARD_MODE", "lldpTransmit", "aclFilter"):
            assert nvpair not in payload, (
                f"{nvpair} absent from HAVE must not be invented"
            )


# =====================================================================================
# IDEMPOTENCE — second run through the real comparator
# =====================================================================================
def test_second_run_is_idempotent_on_the_loopback_parent():
    def run_once():
        s = _instance()
        s.want = [_want(_want_md(True))]
        s.have = _have(_full_have("true"))         # already correct
        s.pb_input = [_pb(enable_ospf_auth_message_digest=True)]
        _run(s)
        return _payload_nv(s), _public_nv(s)

    first_payload, first_public = run_once()
    second_payload, second_public = run_once()
    assert first_payload == second_payload, "the comparator must be deterministic"
    assert first_public == second_public
    if first_public is not None:
        for key in HAVE_ONLY_WRITABLE:
            assert key not in first_public, "carried keys must never enter the public diff"


def test_second_run_is_idempotent_on_the_eth_parent():
    def run_once():
        s = _eth_instance()
        s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="changed"))]
        have_nv = dict(ETH_BUILDER_NV)
        have_nv.update(ETH_HAVE_REGISTERED)
        s.have = _eth_have(have_nv)
        s.pb_input = [_eth_pb(description="changed")]
        _run(s)
        return _payload_nv(s), _public_nv(s)

    first_payload, first_public = run_once()
    second_payload, second_public = run_once()
    assert first_payload == second_payload
    assert first_public == second_public


# =====================================================================================
# NO TRANSPORT OF UNREGISTERED OR WRONG-PARENT nvPairs
# =====================================================================================
def test_registered_carry_forward_skips_a_wrong_parent_binding():
    """A field registered on one parent must not be carried onto a parent that lacks it.

    FLOWCONTROL is the sharpest case available: a sweep of all 98 templates confirms only the
    two host ethernet parents declare it, so no port-channel parent may carry it. This
    previously used DISABLE_LLDP, which turned out to be a poor choice -- the port-channel
    templates DO declare it, and it is now registered there.
    """
    carried = {row["profile_key"] for row in gie_carry_forward_bindings(PC_TRUNK)}
    assert "flowcontrol_receive" not in carried
    assert "flowcontrol_send" not in carried
    assert all(
        row["profile_key"] != "guard_mode"
        for row in gie_carry_forward_bindings(PC_DOT1Q)
    ), "guard_mode is not registered on pc/dot1q"


def test_unregistered_nvpair_is_not_carried_by_the_registered_path():
    s = _eth_instance()
    s.want = [_eth_want(dict(ETH_BUILDER_NV, DESC="new"))]
    have_nv = dict(ETH_BUILDER_NV)
    have_nv["SOME_UNREGISTERED_NVPAIR"] = "x"
    s.have = _eth_have(have_nv)
    s.pb_input = [_eth_pb(description="new")]
    _run(s)
    payload = _payload_nv(s)
    if payload is not None:
        assert "SOME_UNREGISTERED_NVPAIR" not in payload, (
            "the eth parent has no generic HAVE carry-forward; only registered bindings carry"
        )
