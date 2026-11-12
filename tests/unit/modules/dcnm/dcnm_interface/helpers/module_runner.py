"""Real-main test case for dcnm_interface that mocks only the external boundary."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_ENABLED_PATCH_VERSIONS
from ...dcnm_module import TestDcnmModule, set_module_args
from .fixture_cases import load_case


SUPPORTED = "12.6.0.267"


# The module-path runner declares this explicitly for every caller, so every pre-existing
# fixture keeps exercising the NDFC-version boundary it was written for, unaffected by the
# new, additional patch boundary.
SUPPORTED_PATCH = sorted(GIE_ENABLED_PATCH_VERSIONS)[0]


class A161Base(TestDcnmModule):
    """Shared mocking. Mirrors TestDcnmIntfModule.setUp so the real module path runs."""

    module = dcnm_interface
    ndfc_version = SUPPORTED

    def setUp(self):
        super(A161Base, self).setUp()
        self.config_data = load_case("dcnm_intf_binding_configs")

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
    def run_config(self, key, state="merged", changed=False, failed=False,
                   patch_version=SUPPORTED_PATCH):
        args = dict(state=state, fabric="test_fabric",
                    config=self.config_data.get(key))
        if patch_version is not None:
            args["patch_version"] = patch_version
        set_module_args(args)
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
