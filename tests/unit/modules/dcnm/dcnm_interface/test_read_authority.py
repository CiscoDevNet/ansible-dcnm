"""Authoritative HAVE reads: bulk/individual GET contract, vPC records, undeployed parents and sweep scope."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import contextlib
import copy
import io
import json
import pytest
import types

from unittest import mock
from ansible.module_utils.connection import ConnectionError as AnsibleConnectionError
from ansible.errors import AnsibleConnectionFailure
from ansible_collections.cisco.dcnm.plugins.httpapi.dcnm import HttpApi
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm as dcnm_utils
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from unittest.mock import patch
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleFailJson
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import ModuleTestCase
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .helpers.have_reader import DcnmIntf
from .helpers.have_reader import _assert_zero_mutating_calls
from .helpers.have_reader import _stub
from .helpers import binding_harness as H
from ..dcnm_module import set_module_args
from .helpers.override_scope import SERIAL
from .helpers.override_scope import _FailJson
from .helpers.override_scope import _have as _override_have
from .helpers.override_scope import _run as _override_run
from .helpers.override_scope import _stub as _override_stub


# ====================================================================================================
# Formerly test_dcnm_intf_have_fetch_contract.py
# The authoritative HAVE response contract: bulk and individual GET handling.
#
# Malformed or failed controller state must never be turned into absence, and authority is
# tracked per (serial, interface) key. Direct method tests patching module-level dcnm_send.
#
# Renamed from test_dcnm_intf_ospfmd_have_fetch.py. The old name was misleading even before the
# OSPF-MD retirement: of its tests only the policy-mismatch guard cases were OSPF-specific, and
# the rest -- the ones here -- are the shared HAVE machinery every parent depends on. Those guard
# cases went with the loopback OSPF-auth bindings they protected; these did not, and must not.
# ====================================================================================================
NVPAIR = "ENABLE_OSPF_AUTH_MESSAGE_DIGEST"
PARENT = "int_fabric_loopback_11_1"


def _ok(data):
    return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": data}


def _lo_group(if_name="Loopback0", nv=None, serial="SN1", policy=PARENT):
    return {"policy": policy, "interfaces": [
        {"ifName": if_name, "serialNumber": serial,
         "nvPairs": {"IP": "192.0.2.1"} if nv is None else nv}]}


def _typed_group(if_name, serial, interface_type, policy=PARENT):
    group = _lo_group(if_name=if_name, serial=serial, policy=policy)
    group["interfaces"][0]["interfaceType"] = interface_type
    return group


def _summary(if_name="Loopback0", serial="SN1"):
    return {
        "ifName": if_name,
        "serialNo": serial,
        "fabricName": "fab",
        "ifType": "INTERFACE_LOOPBACK",
        "isPhysical": False,
        "deletable": True,
        "markDeleted": False,
        "alias": "",
        "deleteReason": None,
        "complianceStatus": "In-Sync",
        "underlayPolicies": [],
    }


def _patch(resp):
    return mock.patch.multiple(
        dcnm_interface, dcnm_send=mock.Mock(return_value=resp), time=mock.Mock())


def _patch_seq(*responses):
    @contextlib.contextmanager
    def patched():
        sender = mock.Mock(side_effect=list(responses))
        with mock.patch.object(dcnm_interface, "dcnm_send", sender), mock.patch.object(
            dcnm_interface, "time", mock.Mock()
        ):
            yield sender
    return patched()


def _patch_exc(exc):
    @contextlib.contextmanager
    def patched():
        sender = mock.Mock(side_effect=exc)
        with mock.patch.object(dcnm_interface, "dcnm_send", sender), mock.patch.object(
            dcnm_interface, "time", mock.Mock()
        ):
            yield sender
    return patched()


@contextlib.contextmanager
def _capture_patch(resp):
    sender = mock.Mock(return_value=resp)
    with mock.patch.object(dcnm_interface, "dcnm_send", sender), mock.patch.object(
        dcnm_interface, "time", mock.Mock()
    ):
        yield sender


def _bulk(s, serial="SN1", refresh=False):
    DcnmIntf.dcnm_intf_bulk_fetch_intf_info(s, serial, refresh=refresh)


def _indiv(s, name="Loopback0", serial="SN1", if_type="INTERFACE_LOOPBACK"):
    return DcnmIntf.dcnm_intf_get_intf_info(s, name, serial, if_type)


# ================================ BULK ======================================
def test_bulk_valid_data_caches_and_authoritative():
    s = _stub()
    with _patch(_ok([_lo_group("Loopback0")])):
        _bulk(s)
    assert "SN1" in s.intf_detail_cached_snos
    assert ("SN1", "loopback0") in s.intf_detail_cache
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is False


def test_bulk_combined_serial_preserves_complete_logical_identity():
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    with _patch(_ok([
        _typed_group("vPC10", "SN1~PEER", "INTERFACE_VPC")
    ])):
        _bulk(s, "SN1~PEER")
    assert ("SN1~PEER", "vpc10") in s.intf_detail_cache


@pytest.mark.parametrize("logical_type", ["INTERFACE_VPC", "AA_FEX"])
def test_bulk_mixed_physical_and_logical_records_commit_atomically(logical_type):
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    groups = [
        _typed_group("Ethernet1/1", "SN1", "INTERFACE_ETHERNET"),
        _typed_group("vPC10", "SN1~PEER", logical_type),
    ]
    with _patch(_ok(groups)):
        _bulk(s, "SN1~PEER")
    assert set(s.intf_detail_cache) == {
        ("SN1", "ethernet1/1"),
        ("SN1~PEER", "vpc10"),
    }
    assert {"SN1", "SN1~PEER"}.issubset(s.intf_detail_cached_snos)
    assert s.intf_detail_fetch_failed_snos == set()


def test_bulk_mixed_wrong_pair_rejects_whole_response():
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    groups = [
        _typed_group("Ethernet1/1", "SN1", "INTERFACE_ETHERNET"),
        _typed_group("vPC10", "SN1~WRONG", "INTERFACE_VPC"),
    ]
    with _patch(_ok(groups)):
        _bulk(s, "SN1~PEER")
    assert s.intf_detail_cache == {}
    assert s.intf_detail_cached_snos == set()
    assert {"SN1~PEER", "SN1", "PEER"}.issubset(
        s.intf_detail_fetch_failed_snos
    )


@pytest.mark.parametrize("physical_serial", ["PEER", "SN1~PEER", "SN1~"])
def test_bulk_mixed_malformed_physical_serial_rejects_whole_response(
    physical_serial,
):
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    groups = [
        _typed_group(
            "Ethernet1/1", physical_serial, "INTERFACE_ETHERNET"
        ),
        _typed_group("vPC10", "SN1~PEER", "INTERFACE_VPC"),
    ]
    with _patch(_ok(groups)):
        _bulk(s, "SN1~PEER")
    assert s.intf_detail_cache == {}
    assert s.intf_detail_cached_snos == set()


@pytest.mark.parametrize("duplicate_type", ["physical", "logical"])
def test_bulk_mixed_duplicate_identity_rejects_whole_response(duplicate_type):
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    physical = _typed_group("Ethernet1/1", "SN1", "INTERFACE_ETHERNET")
    logical = _typed_group("vPC10", "SN1~PEER", "INTERFACE_VPC")
    duplicate = copy.deepcopy(physical if duplicate_type == "physical" else logical)
    duplicate["interfaces"][0]["ifName"] = (
        duplicate["interfaces"][0]["ifName"].lower()
    )
    with _patch(_ok([physical, logical, duplicate])):
        _bulk(s, "SN1~PEER")
    assert s.intf_detail_cache == {}
    assert s.intf_detail_cached_snos == set()
    assert "SN1~PEER" in s.intf_detail_fetch_failed_snos


def test_bulk_mixed_failed_response_replaces_prior_authority_with_failure():
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    s.intf_detail_cache[("SN1", "ethernet1/1")] = _lo_group(
        "Ethernet1/1", serial="SN1"
    )
    s.intf_detail_cache[("SN1~PEER", "vpc10")] = _lo_group(
        "vPC10", serial="SN1~PEER"
    )
    s.intf_detail_cached_snos.update({"SN1", "SN1~PEER"})
    with _patch({"RETURN_CODE": 500}):
        _bulk(s, "SN1~PEER", refresh=True)
    assert s.intf_detail_cache == {}
    assert s.intf_detail_cached_snos == set()
    assert {"SN1~PEER", "SN1", "PEER"}.issubset(
        s.intf_detail_fetch_failed_snos
    )


def test_get_have_prefers_pair_context_for_one_mixed_bulk_query():
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    physical = _typed_group(
        "Ethernet1/1", "SN1", "INTERFACE_ETHERNET"
    )["interfaces"][0]
    logical = _typed_group(
        "vPC10", "SN1~PEER", "INTERFACE_VPC"
    )["interfaces"][0]
    s.want = [
        {"policy": "int_access_host", "interfaces": [physical]},
        {"policy": "int_vpc_trunk_host", "interfaces": [logical]},
    ]
    s.have = []
    s.dcnm_intf_bulk_fetch_intf_info = (
        lambda serial, refresh=False:
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(s, serial, refresh)
    )
    s.dcnm_intf_get_intf_info_from_dcnm = (
        lambda intf: DcnmIntf.dcnm_intf_get_intf_info(
            s,
            intf["ifName"],
            intf["serialNumber"],
            intf["interfaceType"],
        )
    )
    response = _ok([
        {"policy": "int_access_host", "interfaces": [physical]},
        {"policy": "int_vpc_trunk_host", "interfaces": [logical]},
    ])
    with _capture_patch(response) as sender:
        DcnmIntf.dcnm_intf_get_have(s)
    assert sender.call_count == 1
    assert sender.call_args.args[2] == "/if/SN1"
    assert len(s.have) == 2


@pytest.mark.parametrize("if_type", ["INTERFACE_VPC", "AA_FEX"])
def test_bulk_combined_vpc_or_aafex_rejects_single_serial_detail(if_type):
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    group = _lo_group(serial="SN1")
    group["interfaces"][0]["interfaceType"] = if_type
    with _patch(_ok([group])):
        _bulk(s, "SN1~PEER")
    assert s.intf_detail_cache == {}
    assert {"SN1~PEER", "SN1", "PEER"}.issubset(
        s.intf_detail_fetch_failed_snos
    )


def test_bulk_valid_empty_list_is_authoritative_absence():
    s = _stub()
    with _patch(_ok([])):
        _bulk(s)
    assert "SN1" in s.intf_detail_cached_snos
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback9", "SN1") is False


def test_bulk_bare_empty_body_is_authoritative_absence():
    s = _stub()
    with _patch([]):
        _bulk(s)
    assert "SN1" in s.intf_detail_cached_snos
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is False


@pytest.mark.parametrize("resp", [
    {"RETURN_CODE": 500, "DATA": {}},                          # non-200
    {"RETURN_CODE": 200},                                       # missing DATA
    {"RETURN_CODE": 200, "DATA": None},                         # null DATA
    {"RETURN_CODE": 200, "DATA": {"a": 1}},                     # mapping DATA
    {"RETURN_CODE": 200, "DATA": "x"},                          # scalar DATA
    {"RETURN_CODE": 200, "DATA": [42]},                         # malformed group
    {"RETURN_CODE": 200, "DATA": [{"policy": PARENT}]},         # group missing interfaces
    {"RETURN_CODE": 200, "DATA": [{"policy": PARENT, "interfaces": "x"}]},  # interfaces not list
    {"RETURN_CODE": 200, "DATA": [{"policy": PARENT, "interfaces": [7]}]},  # interface not dict
    {"RETURN_CODE": 200, "DATA": [{"policy": PARENT, "interfaces": [{"ifName": ""}]}]},  # empty name
])
def test_bulk_malformed_is_unavailable_not_cached(resp):
    s = _stub()
    with _patch(resp):
        _bulk(s)
    assert "SN1" not in s.intf_detail_cached_snos
    assert "SN1" in s.intf_detail_fetch_failed_snos
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is True


def test_bulk_malformed_does_not_partial_cache():
    # one good group then a malformed one: NOTHING is cached, serial unavailable.
    s = _stub()
    with _patch(_ok([_lo_group("Loopback0"), {"policy": PARENT, "interfaces": [7]}])):
        _bulk(s)
    assert ("SN1", "loopback0") not in s.intf_detail_cache
    assert "SN1" not in s.intf_detail_cached_snos
    assert "SN1" in s.intf_detail_fetch_failed_snos


@pytest.mark.parametrize("group", [
    {"interfaces": [_lo_group()["interfaces"][0]]},
    {"policy": "", "interfaces": [_lo_group()["interfaces"][0]]},
    {"policy": 7, "interfaces": [_lo_group()["interfaces"][0]]},
    {"policy": PARENT, "interfaces": []},
    {"policy": PARENT, "interfaces": [{"ifName": "Loopback0", "nvPairs": {}}]},
    {"policy": PARENT, "interfaces": [{"ifName": "Loopback0", "serialNumber": 7, "nvPairs": {}}]},
    _lo_group(serial="WRONG"),
    {"policy": PARENT, "interfaces": [{"ifName": "Loopback0", "serialNumber": "SN1"}]},
    _lo_group(nv="bad"),
])
def test_bulk_rejects_incomplete_authoritative_identity(group):
    s = _stub()
    with _patch(_ok([group])):
        _bulk(s)
    assert s.intf_detail_cache == {}
    assert "SN1" not in s.intf_detail_cached_snos
    assert "SN1" in s.intf_detail_fetch_failed_snos


@pytest.mark.parametrize("groups", [
    [_lo_group("Loopback0", {"A": 1}), _lo_group("Loopback0", {"A": 2})],
    [_lo_group("Loopback0"), _lo_group("loopback0")],
    [{"policy": PARENT, "interfaces": [
        _lo_group("Loopback0")["interfaces"][0],
        _lo_group("loopback0")["interfaces"][0],
    ]}],
])
def test_bulk_rejects_duplicate_normalized_identity_atomically(groups):
    s = _stub()
    with _patch(_ok(groups)):
        _bulk(s)
    assert s.intf_detail_cache == {}
    assert "SN1" in s.intf_detail_fetch_failed_snos


# ============================= INDIVIDUAL ===================================
def test_individual_valid_data_caches():
    s = _stub()
    with _patch(_ok([_lo_group("Loopback0")])):
        got = _indiv(s)
    assert got and got["interfaces"][0]["ifName"] == "Loopback0"
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is False


def test_individual_combined_serial_requires_complete_logical_identity():
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    with _patch(_ok([_lo_group(serial="SN1~PEER")])):
        got = _indiv(s, serial="SN1~PEER", if_type="INTERFACE_VPC")
    assert got["interfaces"][0]["serialNumber"] == "SN1~PEER"


@pytest.mark.parametrize("response_serial", [
    "SN1~WRONG", "PEER~SN1", "SN1~", "SN1~~PEER", "SN1~PEER~EXTRA",
])
def test_combined_serial_rejects_wrong_reversed_empty_and_extra_components(
    response_serial,
):
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    with _patch(_ok([_lo_group(serial=response_serial)])):
        assert _indiv(s, serial="SN1~PEER", if_type="INTERFACE_VPC") == []
    assert ("SN1~PEER", "loopback0") in s.intf_detail_failed_keys


def test_combined_serial_identity_is_case_insensitive_but_order_sensitive():
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~Peer"}
    with _patch(_ok([_lo_group(serial="sn1~PEER")])):
        got = _indiv(s, serial="SN1~Peer", if_type="AA_FEX")
    assert got["interfaces"][0]["serialNumber"] == "sn1~PEER"


def test_individual_valid_empty_is_authoritative_absence():
    s = _stub()
    with _patch(_ok([])):
        assert _indiv(s) == []
    assert ("SN1", "loopback0") in s.intf_detail_authoritative_absent_keys
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is False


def test_individual_bare_empty_is_authoritative_absence():
    s = _stub()
    with _patch([]):
        assert _indiv(s) == []
    assert ("SN1", "loopback0") in s.intf_detail_authoritative_absent_keys
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is False


@pytest.mark.parametrize("resp", [
    {"RETURN_CODE": 500},                                       # non-200
    {"RETURN_CODE": 200},                                       # missing DATA
    {"RETURN_CODE": 200, "DATA": None},                         # null DATA
    {"RETURN_CODE": 200, "DATA": {"a": 1}},                     # mapping DATA
    {"RETURN_CODE": 200, "DATA": [_lo_group("Loopback0"), _lo_group("Loopback0")]},  # ambiguous
    {"RETURN_CODE": 200, "DATA": [_lo_group("LoopbackX")]},     # wrong identity
])
def test_individual_malformed_is_unavailable(resp):
    s = _stub()
    with _patch(resp):
        assert _indiv(s) == []
    assert ("SN1", "loopback0") in s.intf_detail_failed_keys
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is True


@pytest.mark.parametrize("entry", [
    {"interfaces": [_lo_group()["interfaces"][0]]},
    _lo_group(policy=""),
    _lo_group(policy=7),
    {"policy": PARENT, "interfaces": [{"ifName": "Loopback0", "nvPairs": {}}]},
    _lo_group(serial="WRONG"),
    {"policy": PARENT, "interfaces": [{"ifName": "Loopback0", "serialNumber": "SN1"}]},
    _lo_group(nv="bad"),
    {"policy": PARENT, "interfaces": []},
    {"policy": PARENT, "interfaces": [
        _lo_group("Loopback0")["interfaces"][0],
        _lo_group("loopback0")["interfaces"][0],
    ]},
])
def test_individual_rejects_incomplete_or_ambiguous_identity(entry):
    s = _stub()
    with _patch(_ok([entry])):
        assert _indiv(s) == []
    assert ("SN1", "loopback0") in s.intf_detail_failed_keys


def test_individual_transport_exception_then_success():
    s = _stub()
    with _patch_seq(AnsibleConnectionError("boom"), _ok([_lo_group("Loopback0")])) as sender:
        got = _indiv(s)
    assert got and got["interfaces"][0]["ifName"] == "Loopback0"
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is False
    assert sender.call_count == 2


def test_individual_transport_exceptions_exhaust_is_unavailable():
    s = _stub()
    with _patch_exc(AnsibleConnectionError("boom")) as sender:
        assert _indiv(s) == []
    assert ("SN1", "loopback0") in s.intf_detail_failed_keys
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is True
    assert sender.call_count == 3


@pytest.mark.parametrize("error", [TypeError("bug"), AssertionError("bug")])
def test_individual_programmer_errors_propagate_without_retry(error):
    s = _stub()
    with _patch_exc(error) as sender:
        with pytest.raises(type(error)):
            _indiv(s)
    assert sender.call_count == 1


def _real_httpapi_path(s, *effects):
    low_level = mock.Mock()
    low_level._url = "https://example.invalid"
    low_level.send.side_effect = list(effects)
    httpapi = HttpApi(low_level)
    httpapi.connection = low_level
    httpapi.check_url_connection = mock.Mock()
    proxy = types.SimpleNamespace(send_request=httpapi.send_request)
    s.module._socket_path = "/tmp/not-used"
    return low_level, mock.patch.object(
        dcnm_utils, "Connection", return_value=proxy
    )


def _http_response(data):
    response = mock.Mock()
    response.getcode.return_value = 200
    response.geturl.return_value = "/if/SN1/Loopback0"
    response.msg = "OK"
    return response, io.BytesIO(json.dumps(data).encode())


@pytest.mark.parametrize("error", [TypeError("bug"), AssertionError("bug")])
def test_real_httpapi_to_module_retry_path_propagates_programmer_error_once(error):
    s = _stub()
    low_level, connection_patch = _real_httpapi_path(s, error)
    with connection_patch:
        with pytest.raises(type(error), match="bug"):
            _indiv(s)
    assert low_level.send.call_count == 1


def test_real_httpapi_to_module_retry_path_retries_transport_once():
    s = _stub()
    low_level, connection_patch = _real_httpapi_path(
        s,
        AnsibleConnectionFailure("transport"),
        _http_response([_lo_group()]),
    )
    with connection_patch:
        got = _indiv(s)
    assert got["interfaces"][0]["ifName"] == "Loopback0"
    assert low_level.send.call_count == 2


# ===================== SEQUENCE: per-key authority ==========================
def test_bulk_fail_then_individual_data_for_A_only_A_authoritative():
    s = _stub()
    with _patch({"RETURN_CODE": 500}):   # bulk fails for the whole serial
        _bulk(s)
    with _patch(_ok([_lo_group("Loopback0")])):   # individual A succeeds
        _indiv(s, "Loopback0")
    # A is authoritative; B on the same switch stays unavailable until read
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is False
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback1", "SN1") is True
    # the serial-wide bulk failure was NOT cleared
    assert "SN1" in s.intf_detail_fetch_failed_snos


def test_bulk_fail_then_individual_empty_for_A_A_absent_B_unavailable():
    s = _stub()
    with _patch({"RETURN_CODE": 500}):
        _bulk(s)
    with _patch(_ok([])):
        _indiv(s, "Loopback0")
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is False
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback1", "SN1") is True


def test_bulk_fail_then_individual_fail_for_A_both_unavailable():
    s = _stub()
    with _patch({"RETURN_CODE": 500}):
        _bulk(s)
    with _patch({"RETURN_CODE": 500}):
        _indiv(s, "Loopback0")
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is True
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback1", "SN1") is True


def test_separate_switch_state_is_isolated():
    s = _stub()
    with _patch({"RETURN_CODE": 500}):
        _bulk(s)   # SN1 bulk fails
    # a different switch never touched -> not unavailable (no failure evidence)
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN2") is False
    assert s.dcnm_intf_ospf_md_have_unavailable("Loopback0", "SN1") is True


# ===================== WS3: policy-mismatch guard shape =====================
def _want(nvpairs):
    return {"policy": PARENT, "interfaces": [
        {"ifName": "Loopback0", "serialNumber": "SN1", "fabricName": "fab",
         "nvPairs": nvpairs}]}


def _have(policy, nvpairs, if_name="Loopback0", serial="SN1"):
    return {"policy": policy, "interfaces": [
        {"ifName": if_name, "serialNumber": serial, "nvPairs": nvpairs}]}


def _run_guard(s, want, have):
    s.module.fail_json.side_effect = SystemExit
    try:
        DcnmIntf.dcnm_intf_ospf_md_guard_policy_mismatch(
            s, want, have, "Loopback0", "SN1", "fab")
        return False
    except SystemExit:
        return True


def test_invalidate_serial_authority_removes_only_target_serial():
    s = _stub()
    s.intf_detail_cache = {
        ("SN1", "loopback0"): {"x": 1}, ("SN2", "loopback0"): {"x": 2}
    }
    s.intf_detail_cached_snos = {"SN1", "SN2"}
    s.intf_detail_fetch_failed_snos = {"SN1", "SN2"}
    s.intf_detail_failed_keys = {("SN1", "loopback1"), ("SN2", "loopback1")}
    s.intf_detail_authoritative_absent_keys = {
        ("SN1", "loopback2"), ("SN2", "loopback2")
    }
    s.dcnm_intf_invalidate_serial_authority("SN1~PEER")
    assert all(key[0] == "SN2" for key in s.intf_detail_cache)
    assert s.intf_detail_cached_snos == {"SN2"}
    assert s.intf_detail_fetch_failed_snos == {"SN2"}
    assert s.intf_detail_failed_keys == {("SN2", "loopback1")}
    assert s.intf_detail_authoritative_absent_keys == {("SN2", "loopback2")}


def test_invalidate_then_success_rebuilds_authority():
    s = _stub()
    s.intf_detail_authoritative_absent_keys.add(("SN1", "loopback0"))
    s.dcnm_intf_invalidate_serial_authority("SN1")
    with _patch(_ok([_lo_group()])):
        _bulk(s)
    assert ("SN1", "loopback0") in s.intf_detail_cache
    assert "SN1" in s.intf_detail_cached_snos


def test_bulk_cache_reuse_does_not_refresh_or_discard_authority():
    s = _stub()
    with _patch_seq(_ok([_lo_group()]), _ok([])) as sender:
        _bulk(s)
        _bulk(s)
    assert sender.call_count == 1
    assert ("SN1", "loopback0") in s.intf_detail_cache


def test_explicit_bulk_refresh_atomically_replaces_found_with_empty():
    s = _stub()
    with _patch_seq(_ok([_lo_group()]), _ok([])):
        _bulk(s)
        _bulk(s, refresh=True)
    assert s.intf_detail_cache == {}
    assert s.intf_detail_authoritative_absent_keys == set()
    assert s.intf_detail_failed_keys == set()
    assert s.intf_detail_fetch_failed_snos == set()
    assert "SN1" in s.intf_detail_cached_snos


def test_explicit_failed_refresh_discards_prior_found_and_absent_authority():
    s = _stub()
    s.intf_detail_cache[("SN1", "loopback0")] = _lo_group()
    s.intf_detail_authoritative_absent_keys.add(("SN1", "loopback1"))
    with _patch({"RETURN_CODE": 500}):
        _bulk(s, refresh=True)
    assert s.intf_detail_cache == {}
    assert s.intf_detail_authoritative_absent_keys == set()
    assert s.intf_detail_fetch_failed_snos == {"SN1"}


def test_failed_combined_refresh_marks_pair_and_both_physical_serials():
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    with _patch({"RETURN_CODE": 500}):
        _bulk(s, "SN1~PEER", refresh=True)
    assert {"SN1~PEER", "SN1", "PEER"}.issubset(
        s.intf_detail_fetch_failed_snos
    )
    assert s.dcnm_intf_detail_unavailable("Ethernet1/1", "SN1") is True
    assert s.dcnm_intf_detail_unavailable("Ethernet1/1", "PEER") is True


def test_simple_refresh_does_not_invalidate_peer_physical_authority():
    s = _stub()
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    s.intf_detail_cache[("PEER", "ethernet1/1")] = _lo_group(
        "Ethernet1/1", serial="PEER"
    )
    s.intf_detail_cached_snos.add("PEER")

    with _patch({"RETURN_CODE": 500}):
        _bulk(s, "SN1", refresh=True)

    assert ("PEER", "ethernet1/1") in s.intf_detail_cache
    assert "PEER" in s.intf_detail_cached_snos
    assert s.dcnm_intf_detail_unavailable("Ethernet1/1", "PEER") is False


@pytest.mark.parametrize("response", [
    {"RETURN_CODE": 500, "DATA": []},
    {"RETURN_CODE": 200},
    {"RETURN_CODE": 200, "DATA": None},
    {"RETURN_CODE": 200, "DATA": [42]},
])
def test_interface_summary_malformed_or_failed_is_unavailable(response):
    s = _stub()
    with _patch(response):
        DcnmIntf.dcnm_intf_get_have_all_with_sno(s, "SN1")
    assert s.have_all == []
    assert s.have_all_cached_snos == set()
    assert s.have_all_failed_snos == {"SN1"}


@pytest.mark.parametrize("missing", [
    "fabricName",
    "ifType",
    "isPhysical",
    "markDeleted",
    "alias",
    "complianceStatus",
    "underlayPolicies",
])
# deleteReason is deliberately absent from this list: it is checked where a decision consumes it, not on every entry
# (see test_delete_reason_scope.py).
def test_interface_summary_rejects_missing_mutation_field(missing):
    s = _stub()
    item = _summary()
    item.pop(missing)
    with _patch(_ok([item])):
        DcnmIntf.dcnm_intf_get_have_all_with_sno(s, "SN1")
    assert s.have_all == []
    assert s.have_all_cached_snos == set()
    assert s.have_all_failed_snos == {"SN1"}


def test_interface_summary_rejects_wrong_serial_identity():
    s = _stub()
    with _patch(_ok([_summary(serial="WRONG")])):
        DcnmIntf.dcnm_intf_get_have_all_with_sno(s, "SN1")
    assert s.have_all == []
    assert s.have_all_failed_snos == {"SN1"}


@pytest.mark.parametrize("response", [
    {"RETURN_CODE": 500, "DATA": []},
    {"RETURN_CODE": 200},
    {"RETURN_CODE": 200, "DATA": "bad"},
    {"RETURN_CODE": 200, "DATA": [{"templateName": "breakout_interface"}]},
])
def test_breakout_summary_malformed_or_failed_is_unavailable(response):
    s = _stub()
    with _patch(response):
        DcnmIntf.dcnm_intf_get_have_all_breakout_interfaces(s, "SN1")
    assert s.have_breakout == []
    assert s.have_breakout_cached_snos == set()
    assert s.have_breakout_failed_snos == {"SN1"}


def test_breakout_unavailable_blocks_creation_before_any_mutating_call():
    s = _stub()
    s.want_breakout = [{
        "interfaces": [{"ifName": "Ethernet1/1", "serialNumber": "SN1"}]
    }]
    s.want = []
    s.have = []
    s.pb_input = []
    s.diff_create_breakout = []
    s.diff_delete_breakout = []
    s.pol_pc_member_types = {12: {}}
    s.dcnm_version = 12
    s.class_name = "DcnmIntf"
    s.log = mock.Mock()
    s.module.params = {"state": "merged"}
    s.module.fail_json.side_effect = RuntimeError("fail_json")
    s.have_breakout_failed_snos.add("SN1")
    with mock.patch.object(dcnm_interface, "dcnm_send") as sender:
        with pytest.raises(RuntimeError, match="fail_json"):
            DcnmIntf.dcnm_intf_compare_want_and_have(s, "merged")
    assert s.diff_create_breakout == []
    _assert_zero_mutating_calls(sender)


def test_summary_unavailable_blocks_deploy_decision():
    s = _stub()
    s.have_all_failed_snos.add("SN1")
    s.module.fail_json.side_effect = RuntimeError("fail_json")
    want = {"interfaces": [{
        "ifName": "Loopback10", "serialNumber": "SN1", "fabricName": "fab"
    }]}
    with pytest.raises(RuntimeError, match="fail_json"):
        DcnmIntf.dcnm_intf_can_be_added(s, want)


@pytest.mark.parametrize("endpoint", ["interface", "breakout"])
def test_summary_not_fetched_is_not_authoritative(endpoint):
    s = _stub()
    s.module.fail_json.side_effect = RuntimeError("fail_json")
    with pytest.raises(RuntimeError, match="fail_json"):
        s.dcnm_intf_require_summary_authority("SN1", endpoint=endpoint)


def test_failed_deployment_summary_refresh_never_redeploys():
    s = _stub()
    s.module.params = {"check_deploy": True}
    s.module.fail_json.side_effect = RuntimeError("fail_json")
    s.have_all = [{
        "ifName": "Loopback10", "serialNo": "SN1", "fabricName": "fab",
        "complianceStatus": "Out-Of-Sync",
    }]
    s.dcnm_intf_get_have_all_with_sno = (
        lambda sno: DcnmIntf.dcnm_intf_get_have_all_with_sno(s, sno)
    )
    with _capture_patch({"RETURN_CODE": 500}) as sender:
        with pytest.raises(RuntimeError, match="fail_json"):
            DcnmIntf.dcnm_intf_check_deployment_status(
                s, [{"ifName": "Loopback10", "serialNumber": "SN1"}]
            )
    _assert_zero_mutating_calls(sender)


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden", "deleted"])
@pytest.mark.parametrize("policy,if_type", [
    ("int_loopback", "INTERFACE_LOOPBACK"),
    ("int_routed_host", "INTERFACE_ETHERNET"),
    ("int_vlan", "INTERFACE_VLAN"),
    ("int_l3_port_channel", "INTERFACE_PORT_CHANNEL"),
    ("int_vpc_trunk_host", "INTERFACE_VPC"),
    ("int_port_channel_aa_fex", "AA_FEX"),
])
def test_mutating_compare_fails_closed_for_unavailable_generic_have(
    state, policy, if_type
):
    s = _stub()
    serial = "SN1~PEER" if if_type in ("INTERFACE_VPC", "AA_FEX") else "SN1"
    s.vpc_ip_sn = {"192.0.2.1": "SN1~PEER"}
    s.want = [{
        "deploy": True,
        "policy": policy,
        "interfaceType": if_type,
        "interfaces": [{
            "ifName": "vPC10" if "VPC" in if_type or if_type == "AA_FEX" else "Loopback10",
            "serialNumber": serial,
            "fabricName": "fab",
            "interfaceType": if_type,
            "nvPairs": {},
        }],
    }]
    s.have = []
    s.have_all = []
    s.pb_input = []
    s.want_breakout = []
    s.have_breakout = []
    s.diff_create_breakout = []
    s.diff_delete_breakout = []
    s.diff_create = []
    s.diff_replace = []
    s.diff_deploy = []
    s.changed_dict = [{state: [], "deploy": []}]
    s.pol_pc_member_types = {12: {}}
    s.dcnm_version = 12
    s.class_name = "DcnmIntf"
    s.log = mock.Mock()
    s.module.params = {"state": state}
    s.module.fail_json.side_effect = RuntimeError("fail_json")
    s.intf_detail_fetch_failed_snos.add(s._dcnm_intf_authority_key(serial))
    with mock.patch.object(dcnm_interface, "dcnm_send") as sender:
        with pytest.raises(RuntimeError, match="fail_json"):
            DcnmIntf.dcnm_intf_compare_want_and_have(s, state)
    assert s.diff_create == []
    assert s.diff_replace == []
    assert s.diff_deploy == []
    _assert_zero_mutating_calls(sender)


@pytest.mark.parametrize("response", [
    {"RETURN_CODE": 500},
    {"RETURN_CODE": 200},
])
def test_invalidate_then_failed_refresh_leaves_unavailable(response):
    s = _stub()
    s.intf_detail_cache[("SN1", "loopback0")] = _lo_group()
    s.intf_detail_authoritative_absent_keys.add(("SN1", "loopback1"))
    s.dcnm_intf_invalidate_serial_authority("SN1")
    with _patch(response):
        _bulk(s)
    assert s.intf_detail_cache == {}
    assert s.dcnm_intf_detail_unavailable("Loopback0", "SN1") is True


def _refresh_stub():
    s = _stub()
    s.deferred_delete_member_defaults = [{
        "ifName": "Ethernet1/1",
        "serialNumber": "SN1",
        "fabricName": "fab",
        "deploy": True,
        "parentIfName": "port-channel10",
    }]
    s._deferred_delete_member_default_keys = {("SN1", "ethernet1/1", "port-channel10")}
    s.have_all = [{
        "ifName": "Ethernet1/1", "serialNo": "SN1", "isPhysical": True
    }]
    s.diff_replace = []
    s.diff_deploy = []
    s.changed_dict = [{"replaced": [], "deploy": []}]
    s.dcnm_intf_get_have_all_with_sno = mock.Mock()
    s.dcnm_intf_parent_present_in_have_all = mock.Mock(return_value=False)
    s.dcnm_intf_get_default_eth_payload = mock.Mock(return_value={
        "policy": "int_access_host", "interfaces": [{"ifName": "Ethernet1/1"}]
    })
    s.dcnm_intf_get_intf_info_from_dcnm = (
        lambda intf: DcnmIntf.dcnm_intf_get_intf_info(
            s, intf["ifName"], intf["serialNumber"], intf["interfaceType"]
        )
    )
    s.dcnm_intf_bulk_fetch_intf_info = (
        lambda sno, refresh=False:
        DcnmIntf.dcnm_intf_bulk_fetch_intf_info(s, sno, refresh=refresh)
    )
    s.dcnm_intf_invalidate_serial_authority = (
        lambda sno: DcnmIntf.dcnm_intf_invalidate_serial_authority(s, sno)
    )
    s.dcnm_intf_detail_unavailable = (
        lambda name, sno: DcnmIntf.dcnm_intf_detail_unavailable(s, name, sno)
    )
    s.dcnm_intf_merge_intf_info = mock.Mock()
    s.dcnm_compare_default_payload = mock.Mock(return_value="DIFF")
    return s


@pytest.mark.parametrize("response", [
    {"RETURN_CODE": 500},
    {"RETURN_CODE": 200},
    AnsibleConnectionError("boom"),
])
def test_deferred_refresh_unavailable_schedules_zero_replacement_or_deploy(response):
    s = _refresh_stub()
    s.intf_detail_cache[("SN1", "ethernet1/1")] = _lo_group("Ethernet1/1")
    patcher = _patch_exc(response) if isinstance(response, BaseException) else _patch(response)
    s.module.fail_json.side_effect = RuntimeError("fail_json")
    with patcher, pytest.raises(RuntimeError, match="fail_json"):
        DcnmIntf.dcnm_intf_refresh_deferred_deleted_member_defaults(s)
    assert s.diff_replace == []
    assert s.diff_deploy == []
    assert s.changed_dict[0]["replaced"] == []
    assert s.changed_dict[0]["deploy"] == []


def test_repeated_failed_refresh_never_leaks_prior_authority():
    s = _refresh_stub()
    for stale in ({"found": True}, {"absent": True}):
        if stale.get("found"):
            s.intf_detail_cache[("SN1", "ethernet1/1")] = _lo_group("Ethernet1/1")
        if stale.get("absent"):
            s.intf_detail_authoritative_absent_keys.add(("SN1", "ethernet1/1"))
        s.module.fail_json.side_effect = RuntimeError("fail_json")
        with _patch({"RETURN_CODE": 500}), pytest.raises(
            RuntimeError, match="fail_json"
        ):
            DcnmIntf.dcnm_intf_refresh_deferred_deleted_member_defaults(s)
        assert s.intf_detail_cache == {}
        assert s.intf_detail_authoritative_absent_keys == set()
        assert s.diff_replace == []
        s.deferred_delete_member_defaults = [{
            "ifName": "Ethernet1/1", "serialNumber": "SN1",
            "fabricName": "fab", "deploy": True,
            "parentIfName": "port-channel10",
        }]


# ====================================================================================================
# Formerly test_dcnm_intf_bulk_vpc_identity.py
# A vPC record in a bulk interface response must not mark its switch unreadable.
#
# The bulk endpoint (``/rest/interface?serialNumber=X``) does NOT return ``interfaceType``.
# Measured against NDFC 12.6.0.267: a vPC record carries exactly ``ifName``, ``nvPairs`` and a
# combined ``serialNumber``, and the item enclosing it carries exactly ``policy`` and
# ``interfaces``. ``_dcnm_intf_bulk_response_identity`` decided the vPC branch on the type alone,
# so every vPC record fell through to the single-serial branch, which rejects a combined serial.
#
# One rejected record marks the WHOLE switch unreadable, and from then on any interface on it
# that reaches the authority gate fails with "could not be read authoritatively".
#
# Interfaces still named in the playbook never noticed: they are in ``want``, so the sweep skips
# the gate for them. The damage only surfaced on a delete-everything run -- ``config: []`` with
# ``state: overridden``, which is what a NAC remove step sends -- where nothing is wanted and the
# gate runs over every interface. It then failed on whichever interface came first, naming an
# interface that was not itself at fault.
#
# Corroborating the pair against ``vpc_ip_sn`` is NOT a usable check here and these tests pin
# that too: that map is only ever populated from switches named in the playbook, so on the very
# run where this breaks it is empty. The check that does the work is that the serial we queried
# is one of the two halves of the returned pair.
#
# Companion to test_read_authority.py, which covers where the gate runs.
# This file covers what makes it fire.
# ====================================================================================================
BulkVpcDcnmIntf = dcnm_interface.DcnmIntf

QUERY = "9P21OHXOL9L"
PEER = "912N7KTAC63"
PAIR = "{0}~{1}".format(QUERY, PEER)
FOREIGN_PAIR = "AAAAAAAAAAA~BBBBBBBBBBB"


def _obj(vpc_ip_sn=None):
    """The helper under test needs no constructed module, only its own state."""
    obj = BulkVpcDcnmIntf.__new__(BulkVpcDcnmIntf)
    obj.vpc_ip_sn = vpc_ip_sn if vpc_ip_sn is not None else {}
    return obj


# The exact shape NDFC returns. interfaceType is absent at BOTH levels -- that absence
# is the whole point, so it is spelled out rather than implied.
REAL_VPC_ITEM = {
    "policy": "int_vpc_trunk_host",
    "interfaces": [
        {
            "ifName": "vpc55",
            "serialNumber": PAIR,
            "nvPairs": {"MEMBER_INTERFACES": "e1/5"},
        }
    ],
}


def test_the_bulk_item_really_has_no_interface_type():
    """Pin the premise: if NDFC ever starts sending it, this test says so first."""
    assert "interfaceType" not in REAL_VPC_ITEM
    assert "interfaceType" not in REAL_VPC_ITEM["interfaces"][0]


def test_a_vpc_record_without_interface_type_resolves():
    """The regression. Before the fix this returned None and poisoned the switch."""
    intf = REAL_VPC_ITEM["interfaces"][0]
    identity = _obj()._dcnm_intf_bulk_response_identity(
        intf["serialNumber"],
        intf.get("interfaceType", REAL_VPC_ITEM.get("interfaceType")),
        QUERY,
        QUERY,
    )
    assert identity == PAIR


def test_resolution_does_not_depend_on_vpc_ip_sn():
    """An empty pair map is the normal state on a delete-everything run.

    If this ever needs vpc_ip_sn populated, the bug is back by another route.
    """
    empty = _obj({})._dcnm_intf_bulk_response_identity(PAIR, None, QUERY, QUERY)
    populated = _obj({"192.0.2.10": PAIR})._dcnm_intf_bulk_response_identity(
        PAIR, None, QUERY, QUERY
    )
    assert empty == populated == PAIR


def test_the_explicit_type_still_resolves():
    """Callers that DO declare the type keep their existing path, unchanged.

    That path corroborates the pair against ``vpc_ip_sn``, so this populates it --
    which is exactly what the pre-existing bulk tests do. The declared path was not
    touched: only the absent-type case changed.
    """
    for declared in ("INTERFACE_VPC", "AA_FEX"):
        obj = _obj({"192.0.2.10": PAIR})
        assert obj._dcnm_intf_bulk_response_identity(PAIR, declared, QUERY, QUERY) == PAIR


def test_a_physical_type_with_a_combined_serial_is_still_malformed():
    """Shape only decides when the type is absent.

    A record that says INTERFACE_ETHERNET and carries a pair serial is malformed --
    a physical port belongs to one switch. Widening the shape rule to cover declared
    types would have silently accepted it; this pins that it does not.
    """
    assert (
        _obj({"192.0.2.10": PAIR})._dcnm_intf_bulk_response_identity(
            PAIR, "INTERFACE_ETHERNET", QUERY, QUERY
        )
        is None
    )


@pytest.mark.parametrize(
    "response_serial,query_serial,expected_serial,why",
    [
        ("ZZZZZZZZZZZ", QUERY, QUERY, "a different switch's serial"),
        (FOREIGN_PAIR, QUERY, QUERY, "a pair that does not contain the queried serial"),
        (PAIR, QUERY, FOREIGN_PAIR, "an explicit pair was asked for, a different one came back"),
        (PAIR, None, QUERY, "no queried serial to check the halves against"),
        (None, QUERY, QUERY, "no serial at all"),
        ("", QUERY, QUERY, "an empty serial"),
        ("A~B~C", QUERY, QUERY, "a malformed three-part serial"),
    ],
)
def test_a_foreign_or_malformed_record_is_still_rejected(
    response_serial, query_serial, expected_serial, why
):
    """The fix must not become a way in. Each of these must still fail closed."""
    assert (
        _obj()._dcnm_intf_bulk_response_identity(
            response_serial, None, query_serial, expected_serial
        )
        is None
    ), why


def test_a_plain_single_serial_record_still_resolves():
    """Non-vPC interfaces are the common case and must be untouched."""
    assert _obj()._dcnm_intf_bulk_response_identity(QUERY, None, QUERY, QUERY) == QUERY


def test_a_single_serial_from_another_switch_is_rejected():
    assert (
        _obj()._dcnm_intf_bulk_response_identity("ZZZZZZZZZZZ", None, QUERY, QUERY)
        is None
    )


# ====================================================================================================
# Formerly test_dcnm_intf_vpc_undeployed_summary.py
# A never-deployed vPC parent is read without a compliance value; it is never In-Sync.
#
# MEASURED (live, NDFC 12.6.0.267, `interface/detail`): a conventional vPC created with ``deploy: false`` shows its LOGICAL parent
# (ifType INTERFACE_VPC, composite serial) with ``complianceStatus`` present and null, while its child port-channels report
# ``Out-of-Sync``. The strict summary reader used to reject the whole switch for that one entry, so the next invocation (deploy, query,
# sweep) was refused as "could not be read authoritatively".
#
# The reader now accepts null ONLY for that shape. Absent key, empty string, a non-string, and null on any other entry or on a single
# serial are still rejected. The null is stored untouched and every consumer keeps comparing against "In-Sync", so convergence is still
# required and an unknown compliance never authorises a deploy by itself.
#
# The vPC parent null in the main() cases is a REPLAY of the measured shape (harness entry with its compliance replaced by null); the
# reader cases are labelled SYNTHETIC where they alter a measured entry to probe a format the capture does not show.
# ====================================================================================================
UndeployedDcnmIntf = dcnm_interface.DcnmIntf
UNDEPLOYED_PAIR = "SN1~SN2"


# ------------------------------------------------------------------ reader
def _entry(name="vPC12", if_type="INTERFACE_VPC", serial=UNDEPLOYED_PAIR, compliance=None, **kw):
    item = {
        "ifName": name, "serialNo": serial, "fabricName": "F", "ifType": if_type, "isPhysical": None, "markDeleted": False,
        "alias": None, "deleteReason": None, "complianceStatus": compliance, "underlayPolicies": [],
    }
    item.update(kw)
    return item


def _undeployed_stub():
    s = types.SimpleNamespace()
    s.have_all = []
    s.have_all_cached_snos = set()
    s.have_all_failed_snos = set()
    s.paths = {"IF_DETAIL_WITH_SNO": "/detail?serialNumber={0}"}
    s.ip_sn = {"192.0.2.1": "SN1", "192.0.2.2": "SN2"}
    s.vpc_ip_sn = {}
    s.module = mock.Mock()
    s._dcnm_intf_authority_key = UndeployedDcnmIntf._dcnm_intf_authority_key
    s._dcnm_intf_query_serial = UndeployedDcnmIntf._dcnm_intf_query_serial
    s._dcnm_intf_serial_parts = UndeployedDcnmIntf._dcnm_intf_serial_parts
    s._dcnm_intf_summary_authorities = lambda sno: set()
    s._dcnm_intf_get_with_retries = mock.Mock()
    return s


def _read(items, sno="SN1", stub=None):
    s = stub or _undeployed_stub()
    s._dcnm_intf_get_with_retries.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": items}
    with mock.patch.object(dcnm_interface, "read_reason_note") as note, mock.patch.object(dcnm_interface, "read_reason_clear"):
        ok = UndeployedDcnmIntf.dcnm_intf_get_have_all_with_sno(s, sno)
    return s, ok, note


def test_measured_undeployed_vpc_parent_is_read_and_stored_untouched():
    child = _entry("Port-channel12", "INTERFACE_PORT_CHANNEL", "SN1", "Out-of-Sync")
    s, ok, note = _read([child, _entry()])
    assert ok is True and note.call_count == 0
    assert s.have_all_failed_snos == set() and s.have_all_cached_snos
    parent = [e for e in s.have_all if e["ifType"] == "INTERFACE_VPC"][0]
    assert parent["complianceStatus"] is None, "no In-Sync (or any other value) may be invented"


def test_in_sync_vpc_parent_control_is_unchanged():
    s, ok, _n = _read([_entry(compliance="In-Sync")])
    assert ok is True and s.have_all[0]["complianceStatus"] == "In-Sync"


@pytest.mark.parametrize("entry,label", [
    (_entry("Port-channel12", "INTERFACE_PORT_CHANNEL", "SN1", None), "null on a port-channel child"),
    (_entry("Ethernet1/5", "INTERFACE_ETHERNET", "SN1", None), "null on a physical member"),
    (_entry(serial="SN1"), "null on an INTERFACE_VPC with a single serial"),
    (_entry(compliance=""), "empty string on the vPC parent"),
    (_entry(compliance=5), "non-string on the vPC parent"),
], ids=lambda v: v if isinstance(v, str) else "")
def test_null_is_not_accepted_outside_the_measured_shape_SYNTHETIC(entry, label):
    s, ok, note = _read([entry])
    assert ok is False, label
    assert s.have_all == [] and s.have_all_failed_snos == {"SN1"}
    assert note.call_args[0][3] == "entry 0: field complianceStatus missing or empty"


def test_absent_compliance_key_on_the_vpc_parent_is_still_rejected_SYNTHETIC():
    entry = _entry()
    del entry["complianceStatus"]
    s, ok, note = _read([entry])
    assert ok is False and s.have_all_failed_snos == {"SN1"}
    assert note.call_args[0][3] == "entry 0: field complianceStatus missing or empty"


def test_a_valid_null_parent_does_not_hide_a_malformed_record_next_to_it():
    bad = _entry("Port-channel12", "INTERFACE_PORT_CHANNEL", "SN1", "In-Sync")
    del bad["alias"]
    s, ok, note = _read([_entry(), bad])
    assert ok is False and s.have_all == [] and s.have_all_failed_snos == {"SN1"}
    assert note.call_args[0][3] == "entry 1: field alias missing"


def test_one_unreadable_switch_stays_failed_while_the_other_is_read():
    s = _undeployed_stub()
    s, ok_a, _n = _read([_entry()], "SN1", s)
    s._dcnm_intf_get_with_retries.return_value = {"RETURN_CODE": 500, "MESSAGE": "boom", "DATA": None}
    with mock.patch.object(dcnm_interface, "read_reason_note"), mock.patch.object(dcnm_interface, "read_reason_clear"):
        ok_b = UndeployedDcnmIntf.dcnm_intf_get_have_all_with_sno(s, "SN2")
    assert ok_a is True and ok_b is False
    assert "SN2" in s.have_all_failed_snos or any("SN2" in x for x in s.have_all_failed_snos)
    with pytest.raises(Exception):
        s.module.fail_json.side_effect = RuntimeError("fail_json")
        UndeployedDcnmIntf.dcnm_intf_require_summary_authority(types.SimpleNamespace(
            module=s.module, have_all_failed_snos=s.have_all_failed_snos, have_all_cached_snos=s.have_all_cached_snos,
            have_breakout_failed_snos=set(), have_breakout_cached_snos=set(),
            _dcnm_intf_authority_key=UndeployedDcnmIntf._dcnm_intf_authority_key), "SN2")


# ------------------------------------------------------------------ real main()
VPC_HAVE = None


def _undeployed_have():
    global VPC_HAVE
    if VPC_HAVE is None:
        VPC_HAVE = H.build_have(H.VPC_TRUNK)
    return copy.deepcopy(VPC_HAVE)


def _conf(deploy=True):
    return H.cfg_for(H.VPC_TRUNK, H.base_for(H.VPC_TRUNK), deploy=deploy)


def _drive(configs, state, converge_after_deploy=False, detail_override=None, check_deploy=False, null_parent=True):
    """Real main() with the harness transport; the vPC parent entry of `interface/detail` is the measured never-deployed shape."""
    calls = []
    have = _undeployed_have()
    base = H._transport(calls, have)
    deployed = {"done": False}

    def send(mod, method, path, payload=None):
        response = base(mod, method, path, payload)
        if method == "POST" and path.endswith("/rest/globalInterface/deploy"):
            deployed["done"] = True
        if method == "GET" and "/interface/detail" in path:
            if detail_override is not None:
                return detail_override(response)
            if null_parent and not (converge_after_deploy and deployed["done"]):
                for entry in response["DATA"]:
                    if entry["ifType"] == "INTERFACE_VPC":
                        entry["complianceStatus"] = None
        return response

    original = H.set_module_args

    def with_args(args):
        args = dict(args)
        if check_deploy:
            args["check_deploy"] = True
        return original(args)

    with mock.patch.object(H, "_transport", lambda _c, _h: send), mock.patch.object(H, "set_module_args", with_args):
        result, _unused = H.run_configs(configs, state, have=have)
    return result, calls


def _writes(calls):
    return [c for c in calls if c["method"] != "GET"]


def _deploys(calls):
    return [c for c in _writes(calls) if c["path"].endswith("/rest/globalInterface/deploy")]


def test_next_invocation_with_deploy_reads_the_parent_and_deploys_it():
    result, calls = _drive([_conf(True)], "merged")
    assert not result.get("failed"), result.get("msg")
    assert len(_deploys(calls)) == 1 and len(_writes(calls)) == 1, "only the deploy; no intent is rewritten"
    assert [i["ifName"] for i in _deploys(calls)[0]["payload"]] == ["vPC12"]


def test_next_invocation_without_deploy_reads_and_writes_nothing():
    result, calls = _drive([_conf(False)], "merged")
    assert not result.get("failed"), result.get("msg")
    assert _writes(calls) == []


def test_query_reads_the_undeployed_parent():
    result, calls = _drive([_conf(True)], "query")
    assert not result.get("failed"), result.get("msg")
    assert _writes(calls) == []


def test_convergence_is_still_required_when_the_parent_stays_unknown():
    result, calls = _drive([_conf(True)], "merged", check_deploy=True)
    assert result["failed"] is True
    assert "did not reach 'In-Sync'" in str(result["msg"])
    assert len(_deploys(calls)) >= 1


def test_convergence_check_passes_once_the_controller_reports_in_sync():
    result, calls = _drive([_conf(True)], "merged", converge_after_deploy=True, check_deploy=True)
    assert not result.get("failed"), result.get("msg")
    assert len(_deploys(calls)) >= 1


def test_malformed_neighbour_entry_still_refuses_the_whole_request_before_any_write():
    def broken(response):
        for entry in response["DATA"]:
            if entry["ifType"] == "INTERFACE_VPC":
                entry["complianceStatus"] = None
        response["DATA"].append({"ifName": "Ethernet1/40"})
        return response

    result, calls = _drive([_conf(True)], "merged", detail_override=broken)
    assert result["failed"] is True and "could not be read authoritatively" in result["msg"]
    assert _writes(calls) == []


def test_sweep_without_config_still_refuses_when_the_summary_is_unreadable():
    def http_500(_response):
        return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": None}

    for state in ("overridden", "deleted"):
        result, calls = _drive([], state, detail_override=http_500)
        assert result.get("failed") is True, (state, result)
        assert _writes(calls) == []


def test_named_delete_of_the_undeployed_vpc_is_unchanged_by_the_reader_fix():
    """Control: this path never depended on the changed check; base and candidate send the same two writes."""
    conf = {"name": "vpc12", "type": "vpc", "switch": ["10.0.0.1", "10.0.0.2"], "deploy": True}
    result, calls = _drive([conf], "deleted")
    assert not result.get("failed"), result.get("msg")
    assert [(c["method"], c["path"].rsplit("/rest/", 1)[-1]) for c in _writes(calls)] == [
        ("DELETE", "interface/markdelete"), ("POST", "globalInterface/deploy")]


# ====================================================================================================
# Formerly test_dcnm_intf_sweep_summary_authority.py
# `overridden` / `deleted` WITHOUT config: the interface summary of every switch is the scope of the sweep.
#
# A switch whose summary could not be read authoritatively (HTTP error, an entry the reader rejects, a transport failure on
# every attempt) used to contribute no interface, so the run ended as a successful no-op -- or swept only the readable
# switches -- over state it never saw. It must now refuse during planning, naming the switch, before any configuration or
# deployment request. A VALID empty summary is still a successful no-op, and a vPC peer covered by the pair's answer is not
# refused. Drives the real main() through a recording transport (no network, no .env); the faults are synthetic.
# ====================================================================================================
FABRIC = "SWEEPFAB"
SWITCHES = {"A": ("192.0.2.11", "SNSWEEP0011", "leaf-a"), "B": ("192.0.2.12", "SNSWEEP0012", "leaf-b")}
STATES = ["overridden", "deleted"]
FAULTS = ["http500", "http500_empty", "invalid", "transport"]
TRUNK_NV = {
    "ADMIN_STATE": "false", "ALLOWED_VLANS": "10", "BPDUGUARD_ENABLED": "no", "CONF": "", "DESC": "", "ENABLE_MIRROR_CONFIG": "false",
    "ENABLE_NETFLOW": "false", "FEC": "auto", "GF": "", "INTF_NAME": "Ethernet1/9", "MTU": "jumbo", "NATIVE_VLAN": "", "NETFLOW_MONITOR": "",
    "POLICY_DESC": "", "POLICY_ID": "POLICY-1", "PORTTYPE_FAST_ENABLED": "true", "PRIORITY": "500", "PTP": "false", "SPEED": "Auto",
    "FABRIC_NAME": FABRIC, "MARK_DELETED": "false", "DUPLEX": "auto", "ENABLE_CDP": "true", "QUEUING_POLICY": "", "ENABLE_PFC": "false",
    "ENABLE_QOS": "false", "QOS_POLICY": "",
}


def _sweep_entry(name, sn, if_type="INTERFACE_ETHERNET", physical="true", drop=()):
    item = {"ifName": name, "serialNo": sn, "fabricName": FABRIC, "ifType": if_type, "isPhysical": physical, "markDeleted": False,
            "alias": "", "deleteReason": None, "complianceStatus": "In-Sync", "underlayPolicies": [], "deletable": True,
            "mgmtIpAddress": "", "interfaceDbId": 1}
    for key in drop:
        item.pop(key)
    return item


def _sweep_summary(mode, sn, extra=()):
    if mode == "valid":
        return {"RETURN_CODE": 200, "MESSAGE": "OK",
                "DATA": [_sweep_entry("Ethernet1/9", sn), _sweep_entry("mgmt0", sn, "INTERFACE_MGMT", "false")] + list(extra)}
    if mode == "valid_empty":
        return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}
    if mode == "http500":
        return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {"error": "synthetic fault"}}
    if mode == "http500_empty":
        return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
    if mode == "invalid":
        return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [_sweep_entry("Ethernet1/9", sn, drop=("ifType",))]}
    if mode == "transport":
        raise AnsibleConnectionError("synthetic transport failure")
    raise ValueError(mode)


def _sweep_have(sn):
    return [{"policy": "int_trunk_host", "interfaces": [{"ifName": "Ethernet1/9", "serialNumber": sn, "interfaceType": "INTERFACE_ETHERNET",
                                                         "fabricName": FABRIC, "nvPairs": dict(TRUNK_NV)}]}]


class _Case(ModuleTestCase):
    def runTest(self):
        pass


def _run(state, modes, managable=None, pair_extra=None):
    """modes {"A": mode, "B": mode}; pair_extra: entries of B appended to A's VALID answer (a vPC pair answer)."""
    managable = managable or {}
    inventory = {SWITCHES[k][0]: {"logicalName": SWITCHES[k][2], "serialNumber": SWITCHES[k][1], "isVpcConfigured": "False",
                                  "vpcDomain": 0, "switchRole": "leaf", "managable": managable.get(k, "True")} for k in modes}
    ip_sn = {SWITCHES[k][0]: SWITCHES[k][1] for k in modes}
    hn_sn = {SWITCHES[k][2]: SWITCHES[k][1] for k in modes}
    by_sn = {SWITCHES[k][1]: mode for k, mode in modes.items()}
    calls = []

    def send(mod, method, path, payload=None):
        calls.append({"method": method, "path": path, "payload": json.loads(payload) if isinstance(payload, str) and payload else payload})
        if method != "GET":
            return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}
        if "accessmode" in path.lower():
            return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"readonly": False}}
        sn = path.split("serialNumber=")[-1].split("&")[0] if "serialNumber=" in path else None
        if "/interface/detail" in path:
            extra = pair_extra if (pair_extra and sn == SWITCHES["A"][1]) else ()
            return _sweep_summary(by_sn.get(sn, "valid_empty"), sn, extra)
        if "/interface?" in path:
            return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": _sweep_have(sn) if sn in by_sn else []}
        return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": []}

    case = _Case(methodName="runTest")
    case.setUp()
    set_module_args({"state": state, "fabric": FABRIC, "config": []})
    result = None
    try:
        with patch.object(module, "get_fabric_inventory_details", return_value=inventory), \
                patch.object(module, "get_ip_sn_dict", return_value=(ip_sn, hn_sn)), \
                patch.object(module, "dcnm_version_supported", return_value=(12, "12.6.0.267")), \
                patch.object(module, "dcnm_get_bulk_api_support", return_value=False), \
                patch.object(module, "dcnm_send", side_effect=send), \
                patch.object(module.time, "sleep"):
            try:
                module.main()
            except (AnsibleExitJson, AnsibleFailJson) as exc:
                result = exc.args[0]
            else:
                raise AssertionError("module did not exit through Ansible")
    finally:
        case.tearDown()
    return result, calls


def _serials_written(calls):
    out = set()
    for call in _writes(calls):
        body = call["payload"] if isinstance(call["payload"], list) else [call["payload"]]
        for elem in body:
            for intf in (elem.get("interfaces") or [elem]) if isinstance(elem, dict) else []:
                if isinstance(intf, dict) and intf.get("serialNumber"):
                    out.add(intf["serialNumber"])
    return out


@pytest.mark.parametrize("state", STATES)
def test_valid_summary_with_drift_still_resets_and_deploys(state):
    result, calls = _run(state, {"A": "valid"})
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is True
    assert [c["method"] for c in _writes(calls)] == ["PUT", "POST"]
    assert _serials_written(calls) == {SWITCHES["A"][1]}


@pytest.mark.parametrize("state", STATES)
def test_valid_empty_summary_is_still_a_successful_noop(state):
    result, calls = _run(state, {"A": "valid_empty"})
    assert not result.get("failed"), result.get("msg")
    assert result["changed"] is False and _writes(calls) == []


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("fault", FAULTS)
def test_unreadable_summary_refuses_by_switch_before_any_write_SYNTHETIC(state, fault):
    result, calls = _run(state, {"A": fault})
    assert result.get("failed") is True, "an unreadable summary must not end as a successful no-op"
    assert SWITCHES["A"][1] in result["msg"] and "summary" in result["msg"] and "could not be read authoritatively" in result["msg"]
    assert _writes(calls) == [], "the refusal must precede every configuration or deployment request"


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("fault", FAULTS)
def test_one_unreadable_switch_blocks_the_whole_sweep_before_any_write_SYNTHETIC(state, fault):
    # Switch A is readable and has real work; B is not readable. Nothing may be sent -- not even A's reset.
    result, calls = _run(state, {"A": "valid", "B": fault})
    assert result.get("failed") is True
    assert SWITCHES["B"][1] in result["msg"] and SWITCHES["A"][1] not in result["msg"]
    assert _writes(calls) == []


@pytest.mark.parametrize("state", STATES)
def test_unmanageable_switch_is_part_of_the_sweep_so_its_unreadable_summary_also_refuses_SYNTHETIC(state):
    # The sweep resets interfaces of every switch of the fabric (an unmanageable one included, see the control below),
    # so an unreadable unmanageable switch is not out of scope.
    result, calls = _run(state, {"A": "valid", "B": "http500"}, managable={"B": "False"})
    assert result.get("failed") is True and SWITCHES["B"][1] in result["msg"]
    assert _writes(calls) == []


@pytest.mark.parametrize("state", STATES)
def test_control_unmanageable_switch_with_drift_is_swept(state):
    result, calls = _run(state, {"A": "valid", "B": "valid"}, managable={"B": "False"})
    assert not result.get("failed"), result.get("msg")
    assert _serials_written(calls) == {SWITCHES["A"][1], SWITCHES["B"][1]}


@pytest.mark.parametrize("state", STATES)
def test_vpc_peer_covered_by_the_pair_answer_is_not_refused(state):
    # A's answer also carries B's interfaces (a paired answer): B is read authoritatively through it, so the sweep must not
    # refuse it. B's own summary would fail if it were requested.
    peer = SWITCHES["B"][1]
    pair = [_sweep_entry("Ethernet1/9", peer), _sweep_entry("mgmt0", peer, "INTERFACE_MGMT", "false")]
    result, calls = _run(state, {"A": "valid", "B": "http500"}, pair_extra=pair)
    assert not result.get("failed"), result.get("msg")
    assert not any("/interface/detail" in c["path"] and peer in c["path"] for c in calls), "the peer was covered by A's answer"
    assert _serials_written(calls) == {SWITCHES["A"][1], peer}


# ====================================================================================================
# Formerly test_dcnm_intf_override_authority_scope.py
# The authority gate must guard mutations, not the enumeration that precedes them.
#
# ``dcnm_intf_get_diff_overridden`` walks ``have_all``: every interface on every switch. It only
# acts on a subset of that walk -- physical Ethernet in one branch, and port-channel, loopback,
# sub-interface, vPC, VLAN and FEX in another. ``INTERFACE_MGMT`` matches neither, so an override
# sweep never creates, deletes, resets or deploys mgmt0.
#
# The gate used to run once at the top of that walk. On a switch whose interface state could not
# be read, it therefore failed on whichever interface came first -- in practice mgmt0 -- and the
# error named an interface the sweep was never going to touch. A NAC remove step running
# ``state: overridden`` with an empty config hit this on every run.
#
# Moving the gate to each mutation decision fixes that, but the fix is only correct if the gate is
# still armed. Both properties are asserted here: an out-of-scope interface must not trip it, and
# an in-scope one on the same unreadable switch still must.
# ====================================================================================================
def test_out_of_scope_mgmt_interface_does_not_trip_the_gate():
    """mgmt0 on an unreadable switch must not fail the sweep.

    INTERFACE_MGMT matches neither branch of the override, so no mutation is ever decided for
    it. Failing here reported an interface that was not at stake and masked whichever one
    actually lacked state.
    """
    stub = _override_stub([_override_have("mgmt0", "INTERFACE_MGMT")])

    _override_run(stub)

    assert stub.module.fail_json.call_count == 0, (
        "the gate fired on mgmt0, an interface the override sweep never touches"
    )
    assert all(bucket == [] for bucket in stub.diff_delete)
    assert stub.diff_deploy == []
    assert stub.changed_dict[0]["deleted"] == []


def test_in_scope_interface_on_the_same_unreadable_switch_still_trips_the_gate():
    """The guard must stay armed -- otherwise the fix is just a removal.

    A port-channel absent from ``want`` is a deletion candidate. Deciding to delete it over
    state the controller never confirmed is exactly what the gate exists to stop.
    """
    stub = _override_stub([_override_have("Port-channel10", "INTERFACE_PORT_CHANNEL")])

    with pytest.raises(_FailJson):
        _override_run(stub)

    msg = stub.module.fail_json.call_args.kwargs["msg"]
    assert "Port-channel10" in msg
    assert "no change was sent" in msg


def test_mgmt_interface_does_not_mask_a_real_gap_on_the_same_switch():
    """With both present, the failure must name the interface actually at stake.

    This is the shape of the reported bug: mgmt0 is walked first, so a top-of-loop gate blamed
    it and the port-channel behind it was never reached.
    """
    stub = _override_stub([
        _override_have("mgmt0", "INTERFACE_MGMT"),
        _override_have("Port-channel10", "INTERFACE_PORT_CHANNEL"),
    ])

    with pytest.raises(_FailJson):
        _override_run(stub)

    msg = stub.module.fail_json.call_args.kwargs["msg"]
    assert "Port-channel10" in msg
    assert "mgmt0" not in msg, "the failure still names the wrong interface"


def test_readable_switch_sweeps_without_the_gate_firing():
    """Nothing above weakens the normal path: readable state proceeds as before."""
    stub = _override_stub([_override_have("Port-channel10", "INTERFACE_PORT_CHANNEL")])
    stub.intf_detail_fetch_failed_snos = set()
    stub.intf_detail_cached_snos = {SERIAL}

    _override_run(stub)

    assert stub.module.fail_json.call_count == 0
    assert stub.changed_dict[0]["deleted"], "an unwanted port-channel should be deleted"


def test_unreadable_summary_refuses_the_sweep_even_when_have_all_is_empty():
    """The summary itself could not be read: have_all is empty for this switch, so no gate inside the walk could fire.
    The sweep must refuse on the summary authority before planning any mutation."""
    stub = _override_stub([])
    stub.have_all_cached_snos = set()
    stub.have_all_failed_snos = {SERIAL}
    with pytest.raises(_FailJson):
        _override_run(stub)
    assert "summary" in str(stub.module.fail_json.call_args)
    assert stub.diff_replace == [] and stub.diff_deploy == []
