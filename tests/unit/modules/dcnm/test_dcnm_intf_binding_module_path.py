"""Production-shaped tests through the real dcnm_interface path.

Every test here enters through the module's
public entry point (`execute_module` -> `main()` -> `dcnm_intf_validate_input()` ->
per-type profile validation via `validate_list_of_dicts` -> builder ->
`gie_contribute_nvpairs` -> WANT -> compare -> payload) with transport and HAVE mocked.

Which layer each group exercises:

  MODULE NORMALIZATION (raw playbook value -> validate_list_of_dicts coercion)
      TestBindingRawTypeOnModulePath.*                — B1: raw type rejected pre-coercion
  WANT / BUILDER / FINAL PAYLOAD
      TestBindingPayloadOnModulePath.*                — value survives into the parent nvPair
  HAVE / DIFF / COMPARE / IDEMPOTENCE
      TestBindingHaveAndCompareOnModulePath.*         — carry-forward, malformed HAVE, no-push
  BASELINE REGRESSION
      TestBindingFrozenContractRegression.*           — OSPF-MD + FLOWCONTROL_RECEIVE

NOT LIVE TESTED IN THIS GENERATION. No controller, Nexus or Jenkins is contacted.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

TRUNK = "int_trunk_host"
ACCESS = "int_access_host"
PC_TRUNK = "int_port_channel_trunk_host"
PC_ACCESS = "int_port_channel_access_host"
PC_DOT1Q = "int_port_channel_dot1q_tunnel_host"

SUPPORTED = "12.6.0.267"
BELOW = "12.6.0.266"


class A161Base(TestDcnmModule):
    """Shared mocking. Mirrors TestDcnmIntfModule.setUp so the real module path runs."""

    module = dcnm_interface
    ndfc_version = SUPPORTED

    def setUp(self):
        super(A161Base, self).setUp()
        self.config_data = loadPlaybookData("dcnm_intf_binding_configs")

        self.mock_fabric_details = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface"
            ".get_fabric_inventory_details"
        )
        self.run_fabric_details = self.mock_fabric_details.start()

        self.mock_ip_sn = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface.get_ip_sn_dict"
        )
        self.run_ip_sn = self.mock_ip_sn.start()

        self.mock_version = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface"
            ".dcnm_version_supported"
        )
        self.run_version = self.mock_version.start()

        self.mock_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface.dcnm_send"
        )
        self.run_send = self.mock_send.start()

        self.mock_template_details = patch(
            "ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm.dcnm_get_template_details"
        )
        self.run_template_details = self.mock_template_details.start()
        self.run_template_details.return_value = None

        self.mock_bulk = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface"
            ".dcnm_get_bulk_api_support"
        )
        self.run_bulk = self.mock_bulk.start()
        self.run_bulk.return_value = False

    def tearDown(self):
        super(A161Base, self).tearDown()
        self.mock_bulk.stop()
        self.mock_template_details.stop()
        self.mock_send.stop()
        self.mock_version.stop()
        self.mock_ip_sn.stop()
        self.mock_fabric_details.stop()

    def load_fixtures(self, response=None, device=""):
        self.run_fabric_details.side_effect = [
            self.config_data.get("mock_fab_inv_data")
        ]
        self.run_ip_sn.side_effect = [[self.config_data.get("mock_ip_sn"), []]]
        self.run_version.side_effect = [(12, self.ndfc_version)]
        self.run_send.side_effect = self._send_side_effect()

    def _send_side_effect(self):
        """Default transport: readonly probe, then empty reads, then successes."""
        ok = self.config_data.get("mock_succ_resp")
        return [
            self.config_data.get("mock_monitor_false_resp"),
            self.config_data.get("mock_empty_bulk"),
            self.config_data.get("mock_have_all"),
        ] + [ok] * 30

    # ---- assertions -------------------------------------------------------
    def run_config(self, key, state="merged", changed=False, failed=False):
        set_module_args(
            dict(state=state, fabric="test_fabric",
                 config=self.config_data.get(key))
        )
        return self.execute_module(changed=changed, failed=failed)

    def assert_no_mutating_calls(self):
        """No POST/PUT/DELETE reached the (mocked) controller."""
        for call in self.run_send.call_args_list:
            if len(call.args) >= 2:
                assert str(call.args[1]).upper() in ("GET",), (
                    f"unexpected mutating call: {call.args[1]}"
                )

    def sent_nvpairs(self):
        """{INTF_NAME or ifName: nvPairs} from every payload handed to the transport."""
        found = {}

        def walk(node):
            if isinstance(node, dict):
                if isinstance(node.get("nvPairs"), dict):
                    key = node["nvPairs"].get("INTF_NAME") or node.get("ifName")
                    if key:
                        found[key] = node["nvPairs"]
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        for call in self.run_send.call_args_list:
            if len(call.args) >= 4:
                walk(call.args[3])
        return found

    def diff_nvpairs(self, result, bucket="merged"):
        out = {}
        for d in result["diff"][0][bucket]:
            for intf in d["interfaces"]:
                out[intf["ifName"]] = intf["nvPairs"]
        return out


# =====================================================================================
# B1 — MODULE NORMALIZATION: raw type is enforced BEFORE validate_list_of_dicts coerces
# =====================================================================================
class TestBindingRawTypeOnModulePath(A161Base):
    """Every case the architect reproduced, driven through the real module input path."""

    def _assert_rejected_without_echo(self, result, field, forbidden):
        msg = result["msg"]
        assert "Invalid parameters in playbook" in msg, msg
        assert field in msg, msg
        assert "no change was sent" in msg.lower(), msg
        for token in forbidden:
            assert str(token) not in msg, f"error echoed the rejected value {token!r}: {msg}"

    def test_disable_lldp_string_false_is_rejected_not_coerced_to_False(self):
        result = self.run_config("eth_access_disable_lldp_string_false", failed=True)
        self._assert_rejected_without_echo(result, "disable_lldp", ["'false'", '"false"'])
        assert "native boolean" in result["msg"]
        self.assert_no_mutating_calls()

    def test_disable_lldp_int_one_is_rejected_not_coerced_to_True(self):
        result = self.run_config("eth_access_disable_lldp_int_one", failed=True)
        self._assert_rejected_without_echo(result, "disable_lldp", [])
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

    def test_acl_filter_empty_string_is_rejected_on_length(self):
        result = self.run_config("eth_access_acl_filter_empty", failed=True)
        self._assert_rejected_without_echo(result, "acl_filter", [])
        assert "length 1..64" in result["msg"]
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
        """B1 scope guard: non-registered fields keep their existing legacy behaviour."""
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
        value = self._assert_nvpair(result, "Ethernet1/30", "DISABLE_LLDP", "true")
        assert isinstance(value, str)

    def test_eth_access_disable_lldp_false_reaches_the_parent_nvpair(self):
        """An explicit false is authored intent and must be emitted, not skipped.

        'false' is a value here, never an omission, so the payload must carry the key.
        """
        result = self.run_config("eth_access_disable_lldp_false", changed=True)
        value = self._assert_nvpair(result, "Ethernet1/31", "DISABLE_LLDP", "false")
        assert isinstance(value, str)

    def test_eth_trunk_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("eth_trunk_acl_filter_valid", changed=True)
        value = self._assert_nvpair(result, "Ethernet1/30", "ACL_FILTER", "ACL_ALPHA")
        # Exact type: a str subclass would satisfy isinstance and still be wrong.
        assert type(value) is str  # pylint: disable=unidiomatic-typecheck

    def test_eth_access_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("eth_access_acl_filter_valid", changed=True)
        self._assert_nvpair(result, "Ethernet1/31", "ACL_FILTER", "ACL_BETA")

    def test_pc_trunk_guard_mode_reaches_the_parent_nvpair(self):
        result = self.run_config("pc_trunk_guard_mode_root", changed=True)
        self._assert_nvpair(result, "Port-channel300", "GUARD_MODE", "root")

    def test_pc_trunk_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("pc_trunk_acl_filter_valid", changed=True)
        self._assert_nvpair(result, "Port-channel300", "ACL_FILTER", "ACL_GAMMA")

    def test_pc_access_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("pc_access_acl_filter_valid", changed=True)
        self._assert_nvpair(result, "Port-channel301", "ACL_FILTER", "ACL_DELTA")

    def test_pc_dot1q_acl_filter_reaches_the_parent_nvpair(self):
        result = self.run_config("pc_dot1q_acl_filter_valid", changed=True)
        self._assert_nvpair(result, "Port-channel302", "ACL_FILTER", "ACL_EPS")

    def test_omission_contributes_no_nvpair_and_no_default(self):
        result = self.run_config("eth_trunk_omitted", changed=True)
        merged = self.diff_nvpairs(result)
        # Guard against a vacuous pass: the interface MUST be in the diff, with a real
        # payload, and only then may we assert the absence of the registered nvPairs.
        assert "Ethernet1/30" in merged, f"interface missing from diff: {list(merged)}"
        nvpairs = merged["Ethernet1/30"]
        assert nvpairs, "empty nvPairs would make the absence assertions meaningless"
        assert "INTF_NAME" in nvpairs or "ADMIN_STATE" in nvpairs, sorted(nvpairs)
        for nvpair in ("GUARD_MODE", "DISABLE_LLDP", "ACL_FILTER"):
            assert nvpair not in nvpairs, (
                f"omission produced {nvpair}={nvpairs.get(nvpair)!r}"
            )
        # And nothing reached the wire carrying them either.
        for sent in self.sent_nvpairs().values():
            for nvpair in ("GUARD_MODE", "DISABLE_LLDP", "ACL_FILTER"):
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
        assert merged[ifname]["DISABLE_LLDP"] == "true"

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
        assert merged["Ethernet1/30"]["FLOWCONTROL_RECEIVE"] == "on"

    def test_ospf_md_still_reaches_the_parent_nvpair(self):
        result = self.run_config("lo_fabric_ospfmd_true", changed=True)
        merged = self.diff_nvpairs(result)
        nvpairs = merged.get("Loopback100", {})
        assert nvpairs.get("ENABLE_OSPF_AUTH_MESSAGE_DIGEST") is True
        # Exact type: isinstance(True, int) is True, so isinstance cannot catch a bool
        # degraded to an int.
        assert type(nvpairs["ENABLE_OSPF_AUTH_MESSAGE_DIGEST"]) is bool  # pylint: disable=unidiomatic-typecheck


class TestBindingOspfMdCompatOnUnsupportedVersion(A161Base):
    """The OSPF-MD compat exception must survive: withhold, never fail."""

    ndfc_version = BELOW

    def test_ospf_md_explicit_false_is_withheld_not_failed(self):
        set_module_args(
            dict(
                state="merged",
                fabric="test_fabric",
                config=[{
                    "name": "lo100", "type": "lo", "switch": ["10.0.0.1"],
                    "deploy": False,
                    "profile": {"mode": "fabric", "ipv4_addr": "10.1.1.1",
                                "enable_ospf_auth_message_digest": False},
                }],
            )
        )
        result = self.execute_module(changed=True, failed=False)
        for nvpairs in self.diff_nvpairs(result).values():
            assert "ENABLE_OSPF_AUTH_MESSAGE_DIGEST" not in nvpairs, (
                "the nvPair must be withheld on an unsupported controller"
            )
