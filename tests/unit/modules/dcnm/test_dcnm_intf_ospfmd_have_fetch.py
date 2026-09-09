"""G6A.4.1 WS2 & WS3: authoritative HAVE response contract and policy-mismatch
HAVE shape. Bulk and individual GET handling must never turn malformed or failed
state into absence, authority is tracked per (serial, interface) key, and the
policy-mismatch guard fails closed on a malformed HAVE. Direct method tests
patching module-level dcnm_send.
"""
import contextlib
import copy
import io
import json
import types
from unittest import mock

import pytest
from ansible.module_utils.connection import ConnectionError as AnsibleConnectionError
from ansible.errors import AnsibleConnectionFailure

from ansible_collections.cisco.dcnm.plugins.httpapi.dcnm import HttpApi
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm import dcnm as dcnm_utils
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

DcnmIntf = dcnm_interface.DcnmIntf
NVPAIR = "ENABLE_OSPF_AUTH_MESSAGE_DIGEST"
PARENT = "int_fabric_loopback_11_1"


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
    s.have_all_cached_snos = set()
    s.have_all_failed_snos = set()
    s.have_breakout_cached_snos = set()
    s.have_breakout_failed_snos = set()
    s.have_all = []
    s.have_breakout = []
    s.manageable = {"switch": "SN1"}
    s.fabric = "fab"
    s.vpc_ip_sn = {}
    s._ospf_auth_md_requests = {}
    s._replace_have_lookup = {}
    s._replace_pb_input_lookup = {}
    s.module = mock.Mock()
    s.dcnm_intf_normalize_ospf_auth_message_digest = (
        DcnmIntf.dcnm_intf_normalize_ospf_auth_message_digest
    )
    s._dcnm_intf_valid_individual_entry = DcnmIntf._dcnm_intf_valid_individual_entry
    s._dcnm_intf_ospf_md_matching_interface = DcnmIntf._dcnm_intf_ospf_md_matching_interface
    s._dcnm_intf_ospf_md_matching_interfaces = DcnmIntf._dcnm_intf_ospf_md_matching_interfaces
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
    return s


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


def _assert_zero_mutating_calls(sender):
    assert not any(
        len(call.args) > 1 and call.args[1] in {"POST", "PUT", "DELETE"}
        for call in sender.call_args_list
    )


def test_guard_wellformed_true_fails_closed():
    s = _stub()
    s._ospf_auth_md_requests[("loopback0", "SN1", "fab")] = False
    assert _run_guard(s, _want({"IP": "1"}), _have("int_loopback", {NVPAIR: "true"})) is True
    assert "cannot be cleared across" in s.module.fail_json.call_args.kwargs["msg"]


def test_guard_wellformed_false_is_noop():
    s = _stub()
    s._ospf_auth_md_requests[("loopback0", "SN1", "fab")] = False
    assert _run_guard(s, _want({"IP": "1"}), _have("int_loopback", {NVPAIR: "false"})) is False


def test_guard_wellformed_absent_is_noop():
    s = _stub()
    s._ospf_auth_md_requests[("loopback0", "SN1", "fab")] = False
    assert _run_guard(s, _want({"IP": "1"}), _have("int_loopback", {"IP": "1"})) is False


@pytest.mark.parametrize("have", [
    "not-a-dict",
    {"interfaces": [{"ifName": "Loopback0", "nvPairs": {}}]},          # no policy
    {"policy": "int_loopback"},                                         # no interfaces
    {"policy": "int_loopback", "interfaces": "x"},                      # interfaces not list
    {"policy": "int_loopback", "interfaces": [{"ifName": "LoopbackX", "nvPairs": {}}]},  # wrong identity
    {"policy": "int_loopback", "interfaces": [{"ifName": "Loopback0", "nvPairs": "x"}]},  # malformed nvPairs
    {"policy": "int_loopback", "interfaces": [{"nvPairs": {}}]},        # missing ifName
    _have("int_loopback", {}, serial="WRONG"),
])
def test_guard_malformed_have_fails_closed(have):
    s = _stub()
    s._ospf_auth_md_requests[("loopback0", "SN1", "fab")] = False
    with mock.patch.object(dcnm_interface, "dcnm_send") as sender:
        assert _run_guard(s, _want({"IP": "1"}), have) is True
    assert "could not be determined" in s.module.fail_json.call_args.kwargs["msg"]
    _assert_zero_mutating_calls(sender)


def test_guard_noop_when_value_rides_payload():
    s = _stub()
    s._ospf_auth_md_requests[("loopback0", "SN1", "fab")] = False
    assert _run_guard(s, _want({"IP": "1", NVPAIR: False}),
                      _have("int_loopback", {NVPAIR: "true"})) is False


def test_guard_noop_when_option_omitted():
    s = _stub()
    assert _run_guard(s, _want({"IP": "1"}), _have("int_loopback", {NVPAIR: "true"})) is False


@pytest.mark.parametrize("values", [
    [{NVPAIR: "false"}, {NVPAIR: "true"}],
    [{NVPAIR: "true"}, {NVPAIR: "false"}],
    [{NVPAIR: "false"}, {NVPAIR: "false"}],
])
def test_guard_duplicate_matching_interfaces_fail_closed(values):
    s = _stub()
    s._ospf_auth_md_requests[("loopback0", "SN1", "fab")] = False
    have = {"policy": "int_loopback", "interfaces": [
        {"ifName": "Loopback0", "serialNumber": "SN1", "nvPairs": values[0]},
        {"ifName": "loopback0", "serialNumber": "SN1", "nvPairs": values[1]},
    ]}
    with mock.patch.object(dcnm_interface, "dcnm_send") as sender:
        assert _run_guard(s, _want({"IP": "1"}), have) is True
    _assert_zero_mutating_calls(sender)


def test_guard_one_match_plus_unrelated_interface_is_valid():
    s = _stub()
    s._ospf_auth_md_requests[("loopback0", "SN1", "fab")] = False
    have = _have("int_loopback", {NVPAIR: "false"})
    have["interfaces"].append(
        {"ifName": "Loopback9", "serialNumber": "SN1", "nvPairs": {NVPAIR: "true"}}
    )
    assert _run_guard(s, _want({"IP": "1"}), have) is False


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
    "deleteReason",
    "complianceStatus",
    "underlayPolicies",
])
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
