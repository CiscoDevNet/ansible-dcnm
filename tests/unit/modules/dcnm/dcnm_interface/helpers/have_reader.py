"""HAVE reader stubs shared by the read-authority and read-budget suites."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import types
from unittest import mock
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface


DcnmIntf = dcnm_interface.DcnmIntf


def _stub():
    s = types.SimpleNamespace()
    s.paths = {
        "IF_WITH_SNO": "/if/{}",
        "IF_WITH_SNO_IFNAME": "/if/{}/{}",
        "IF_DETAIL_WITH_SNO": "/detail/{}",
        "GLOBAL_IF_DEPLOY": "/deploy",
    }
    s.intf_detail_cache = {}
    s.intf_detail_cached_snos = set()
    s.intf_detail_fetch_failed_snos = set()
    s.intf_detail_failed_keys = set()
    s.intf_detail_authoritative_absent_keys = set()
    # Consecutive failed policy-detail reads per queried serial. Initialized here
    # because this namespace stands in for an instance without running __init__;
    # the readers use the attribute directly, as production does.
    s.intf_detail_failed_reads = {}
    s.have_all_cached_snos = set()
    s.have_all_failed_snos = set()
    s.have_breakout_cached_snos = set()
    s.have_breakout_failed_snos = set()
    s.have_all = []
    s.have_breakout = []
    s.manageable = {"switch": "SN1"}
    s.fabric = "fab"
    s.vpc_ip_sn = {}
    s._replace_have_lookup = {}
    s._replace_pb_input_lookup = {}
    s.module = mock.Mock()
    # The OSPF-MD helpers this used to wire went with the retired loopback auth capability.
    # Nothing in the HAVE-fetch contract tests depended on them: they were only reachable from
    # the policy-mismatch guard, whose tests were removed with it.
    s._dcnm_intf_valid_individual_entry = DcnmIntf._dcnm_intf_valid_individual_entry
    s._dcnm_intf_normalize_serial = DcnmIntf._dcnm_intf_normalize_serial
    s._dcnm_intf_serial_parts = DcnmIntf._dcnm_intf_serial_parts
    s._dcnm_intf_query_serial = DcnmIntf._dcnm_intf_query_serial
    s._dcnm_intf_authority_key = DcnmIntf._dcnm_intf_authority_key
    s._dcnm_intf_known_pair_identities = (
        lambda: DcnmIntf._dcnm_intf_known_pair_identities(s)
    )
    s._dcnm_intf_summary_authorities = (
        lambda serial: DcnmIntf._dcnm_intf_summary_authorities(s, serial)
    )
    s._dcnm_intf_response_identity = (
        lambda response, query, expected, allow_single=False:
        DcnmIntf._dcnm_intf_response_identity(
            s, response, query, expected, allow_single
        )
    )
    s._dcnm_intf_bulk_response_identity = (
        lambda response, interface_type, query, expected:
        DcnmIntf._dcnm_intf_bulk_response_identity(
            s, response, interface_type, query, expected
        )
    )
    s._dcnm_intf_valid_individual_entry = (
        lambda entry, name, query, expected:
        DcnmIntf._dcnm_intf_valid_individual_entry(
            s, entry, name, query, expected
        )
    )
    s._dcnm_intf_get_with_retries = lambda path: DcnmIntf._dcnm_intf_get_with_retries(s, path)
    s._dcnm_intf_read_budget_key = DcnmIntf._dcnm_intf_read_budget_key
    s._dcnm_intf_read_budget_exhausted = (
        lambda serial: DcnmIntf._dcnm_intf_read_budget_exhausted(s, serial)
    )
    s._dcnm_intf_charge_failed_read = (
        lambda serial: DcnmIntf._dcnm_intf_charge_failed_read(s, serial)
    )
    s._dcnm_intf_clear_failed_reads = (
        lambda serial: DcnmIntf._dcnm_intf_clear_failed_reads(s, serial)
    )
    s.dcnm_intf_ospf_md_have_unavailable = (
        lambda name, sno: DcnmIntf.dcnm_intf_ospf_md_have_unavailable(s, name, sno)
    )
    s._dcnm_intf_ospf_md_have_shape_problem = (
        lambda have, name, sno: DcnmIntf._dcnm_intf_ospf_md_have_shape_problem(s, have, name, sno)
    )
    s.dcnm_intf_detail_unavailable = (
        lambda name, sno: DcnmIntf.dcnm_intf_detail_unavailable(s, name, sno)
    )
    s.dcnm_intf_invalidate_serial_authority = (
        lambda sno: DcnmIntf.dcnm_intf_invalidate_serial_authority(s, sno)
    )
    s.dcnm_intf_require_detail_authority = (
        lambda name, sno: DcnmIntf.dcnm_intf_require_detail_authority(s, name, sno)
    )
    s.dcnm_intf_mark_detail_unavailable = (
        lambda sno: DcnmIntf.dcnm_intf_mark_detail_unavailable(s, sno)
    )
    s.dcnm_intf_require_summary_authority = (
        lambda sno, endpoint="interface":
        DcnmIntf.dcnm_intf_require_summary_authority(s, sno, endpoint)
    )
    # dcnm_intf_get_have registers the controller's secret nvPairs as it assembles HAVE, so the
    # real method is bound here rather than stubbed: a stub would let this harness keep passing
    # while the module stopped protecting key material, which is the failure the HAVE-fetch
    # contract tests would be the last place to notice.
    s.dcnm_intf_register_controller_secrets = (
        lambda payload: DcnmIntf.dcnm_intf_register_controller_secrets(s, payload)
    )
    return s


def _assert_zero_mutating_calls(sender):
    assert not any(
        len(call.args) > 1 and call.args[1] in {"POST", "PUT", "DELETE"}
        for call in sender.call_args_list
    )
