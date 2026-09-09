# Offline tests for the OSPF legacy-key mode on int_fabric_loopback_11_1 (Phase 3, A1.8-legacy-key).
#
# SCOPE: two actual-code paths are driven directly, no AnsibleModule / no live API:
#   * validation -> DcnmIntf.dcnm_intf_validate_ospf_auth_key_input(self.config)
#   * transport  -> DcnmIntf.dcnm_intf_get_loopback_payload(delem, intf, "profile")
# The dedicated validator enforces the full pair, types/range, fabric-loopback-only, and keychain
# exclusion; the builder emits OSPF_AUTH_KEY_ID/OSPF_AUTH_KEY as parent nvPairs (version-gated),
# never fabricating the ospf_interface_auth child (NDFC owns it). The key VALUE is never echoed in an
# error and never printed here (no real secret is used).
#
# NOT COVERED offline (documented as live-validation items): how NDFC returns/encrypts OSPF_AUTH_KEY on
# read-back (key-value idempotency), the effective NX-OS CLI, and OSPF adjacency behavior.
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

DcnmIntf = dcnm_interface.DcnmIntf
KEY_ID_NV = "OSPF_AUTH_KEY_ID"
KEY_NV = "OSPF_AUTH_KEY"
SUPPORTED = "12.6.0.267"
UNSUPPORTED = "12.5.0.100"
# A non-secret placeholder used only to prove the value is transported/never echoed.
PLACEHOLDER_KEY = "PLACEHOLDER_NOT_A_REAL_KEY"


class _FailJson(Exception):
    def __init__(self, msg=None):
        self.msg = msg
        super().__init__(msg)


def _raise(*_a, **kw):
    raise _FailJson(kw.get("msg"))


# ---------------------------------------------------------------- validation --
def _validator(config):
    s = object.__new__(DcnmIntf)
    s.class_name = "DcnmIntf"
    s.log = mock.Mock()
    s.module = mock.Mock()
    s.module.fail_json.side_effect = _raise
    s.config = config
    return s


def _cfg(profile_over=None, type_="lo", mode="fabric", name="Loopback0"):
    prof = {"mode": mode}
    if profile_over:
        prof.update(profile_over)
    return [{"name": name, "type": type_, "profile": prof}]


def test_validate_neither_key_passes():
    _validator(_cfg()).dcnm_intf_validate_ospf_auth_key_input(None)


def test_validate_full_pair_passes():
    cfg = _cfg({"ospf_auth_key_id": 1, "ospf_auth_key": PLACEHOLDER_KEY})
    _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)


def test_validate_key_id_numeric_string_passes():
    cfg = _cfg({"ospf_auth_key_id": "5", "ospf_auth_key": PLACEHOLDER_KEY})
    _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)


def test_validate_only_key_id_fails_full_pair():
    cfg = _cfg({"ospf_auth_key_id": 1})
    with pytest.raises(_FailJson) as e:
        _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)
    assert "together" in e.value.msg


def test_validate_only_key_fails_full_pair():
    cfg = _cfg({"ospf_auth_key": PLACEHOLDER_KEY})
    with pytest.raises(_FailJson) as e:
        _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)
    assert "together" in e.value.msg


def test_validate_key_id_out_of_range_fails():
    cfg = _cfg({"ospf_auth_key_id": 300, "ospf_auth_key": PLACEHOLDER_KEY})
    with pytest.raises(_FailJson) as e:
        _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)
    assert "[0, 255]" in e.value.msg


def test_validate_key_id_bool_rejected():
    # bool is a subclass of int; must be rejected, not treated as 1/0.
    cfg = _cfg({"ospf_auth_key_id": True, "ospf_auth_key": PLACEHOLDER_KEY})
    with pytest.raises(_FailJson):
        _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)


def test_validate_empty_key_fails():
    cfg = _cfg({"ospf_auth_key_id": 1, "ospf_auth_key": ""})
    with pytest.raises(_FailJson) as e:
        _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)
    assert "non-empty string" in e.value.msg


def test_validate_non_loopback_fails():
    cfg = _cfg({"ospf_auth_key_id": 1, "ospf_auth_key": PLACEHOLDER_KEY}, type_="eth")
    with pytest.raises(_FailJson) as e:
        _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)
    assert "fabric loopback" in e.value.msg


def test_validate_non_fabric_mode_fails():
    cfg = _cfg({"ospf_auth_key_id": 1, "ospf_auth_key": PLACEHOLDER_KEY}, mode="lo")
    with pytest.raises(_FailJson) as e:
        _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)
    assert "mode: fabric" in e.value.msg


@pytest.mark.parametrize(
    "kc_key", ["ospf_auth_keychain_name", "ospf_auth_keychain", "ospfAuthKeychainName"]
)
def test_validate_keychain_field_rejected(kc_key):
    cfg = _cfg({kc_key: "KC1"})
    with pytest.raises(_FailJson) as e:
        _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)
    assert "dcnm_fabric" in e.value.msg


def test_validate_error_never_echoes_key_value():
    # An invalid key_id alongside a present key must not leak the key value in the message.
    cfg = _cfg({"ospf_auth_key_id": 999, "ospf_auth_key": PLACEHOLDER_KEY})
    with pytest.raises(_FailJson) as e:
        _validator(cfg).dcnm_intf_validate_ospf_auth_key_input(None)
    assert PLACEHOLDER_KEY not in (e.value.msg or "")


# ----------------------------------------------------------------- transport --
def _lo_instance(version=SUPPORTED):
    s = object.__new__(DcnmIntf)
    s.class_name = "DcnmIntf"
    s.log = mock.Mock()
    s.module = mock.Mock()
    s.module.fail_json.side_effect = _raise
    s.fabric = "fab"
    s.ndfc_version = version
    s._ospf_auth_md_requests = {}
    s.dcnm_intf_get_if_name = mock.Mock(return_value=("Loopback0", "0"))
    s.dcnm_intf_xlate_speed = mock.Mock(return_value="Auto")
    return s


def _delem(**profile_over):
    prof = {
        "mode": "fabric",
        "ipv4_addr": "10.31.0.5",
        "secondary_ipv4_addr": "",
        "ipv6_addr": "",
        "route_tag": "",
        "cmds": None,
        "description": "d",
        "admin_state": True,
        "speed": "Auto",
        "ospf_auth_key_id": None,
        "ospf_auth_key": None,
    }
    prof.update(profile_over)
    return {"name": "Loopback0", "type": "lo", "profile": prof}


def _intf():
    return {"interfaces": [{"nvPairs": {}, "serialNumber": "SN1"}]}


def test_transport_emits_pair_when_supported():
    s = _lo_instance()
    intf = _intf()
    s.dcnm_intf_get_loopback_payload(
        _delem(ospf_auth_key_id=1, ospf_auth_key=PLACEHOLDER_KEY), intf, "profile"
    )
    nv = intf["interfaces"][0]["nvPairs"]
    assert nv[KEY_ID_NV] == "1"
    assert nv[KEY_NV] == PLACEHOLDER_KEY


def test_transport_key_id_is_stringified():
    s = _lo_instance()
    intf = _intf()
    s.dcnm_intf_get_loopback_payload(
        _delem(ospf_auth_key_id=7, ospf_auth_key=PLACEHOLDER_KEY), intf, "profile"
    )
    nv = intf["interfaces"][0]["nvPairs"]
    assert nv[KEY_ID_NV] == "7" and isinstance(nv[KEY_ID_NV], str)


def test_transport_absent_pair_emits_no_key_nvpairs():
    s = _lo_instance()
    intf = _intf()
    s.dcnm_intf_get_loopback_payload(_delem(), intf, "profile")
    nv = intf["interfaces"][0]["nvPairs"]
    assert KEY_ID_NV not in nv and KEY_NV not in nv


def test_transport_never_emits_keychain_nvpair():
    s = _lo_instance()
    intf = _intf()
    s.dcnm_intf_get_loopback_payload(
        _delem(ospf_auth_key_id=1, ospf_auth_key=PLACEHOLDER_KEY), intf, "profile"
    )
    assert "ospfAuthKeychainName" not in intf["interfaces"][0]["nvPairs"]


def test_transport_version_gate_fails_closed_on_unsupported():
    s = _lo_instance(version=UNSUPPORTED)
    intf = _intf()
    with pytest.raises(_FailJson) as e:
        s.dcnm_intf_get_loopback_payload(
            _delem(ospf_auth_key_id=1, ospf_auth_key=PLACEHOLDER_KEY), intf, "profile"
        )
    assert SUPPORTED in e.value.msg
    # fail closed: no key nvPairs leaked into the payload
    assert KEY_ID_NV not in intf["interfaces"][0]["nvPairs"]


# ------------------------------------------- generic input validation (no_log) --
# Regression guard for the live A1.8 failure: dcnm_intf_validate_input ->
# dcnm_intf_validate_loopback_interface_input -> dcnm_intf_validate_interface_input ->
# validate_list_of_dicts(plist, prof_spec) raised
#   "'ospf_auth_key' is a no_log parameter / Ansible module object must be passed..."
# because the AnsibleModule was not passed. These tests exercise that real path (not the
# dedicated validator/transport above, which never reached it).
_COMMON_SPEC = {"name": {"type": "str"}, "profile": {"type": "dict"}}
_PROF_SPEC = {
    "ospf_auth_key_id": {"type": "int"},
    "ospf_auth_key": {"type": "str", "no_log": True},
}


def _intf_input_validator():
    s = object.__new__(DcnmIntf)
    s.class_name = "DcnmIntf"
    s.log = mock.Mock()
    s.module = mock.Mock()
    s.module.fail_json.side_effect = _raise
    # A real set so validate_list_of_dicts can register the scrubbed value.
    s.module.no_log_values = set()
    s.intf_info = []
    return s


def test_generic_validation_passes_module_for_no_log_key():
    # Would raise on the pre-fix code (validate_list_of_dicts called without module).
    s = _intf_input_validator()
    config = [
        {
            "name": "Loopback0",
            "profile": {"ospf_auth_key_id": 17, "ospf_auth_key": PLACEHOLDER_KEY},
        }
    ]
    s.dcnm_intf_validate_interface_input(config, _COMMON_SPEC, _PROF_SPEC)
    # The no_log key value is registered for scrubbing, and no fail_json was raised.
    assert PLACEHOLDER_KEY in s.module.no_log_values
    assert not s.module.fail_json.called


def test_validate_list_of_dicts_contract_requires_module_for_no_log():
    # Pins the dcnm.py contract the fix relies on: a no_log spec param without the module raises.
    from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
        validate_list_of_dicts,
    )

    with pytest.raises(Exception) as e:
        validate_list_of_dicts(
            [{"ospf_auth_key": PLACEHOLDER_KEY}],
            {"ospf_auth_key": {"type": "str", "no_log": True}},
        )
    assert "no_log parameter" in str(e.value)
    # And the error must not echo the key value.
    assert PLACEHOLDER_KEY not in str(e.value)
