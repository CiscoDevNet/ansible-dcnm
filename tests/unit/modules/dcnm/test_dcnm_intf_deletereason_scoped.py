"""deleteReason is required only where a decision consumes it (consumer-scoped validation).

Every case that omits the ``deleteReason`` key is SYNTHETIC: no controller observed so far has omitted it,
so these tests exercise a defensive contract, not a reproduced failure. Absent, ``null`` and text stay
three distinct values.

Consumers of the field in ``dcnm_interface``:

* ``dcnm_intf_get_diff_overridden`` (shared by ``state: overridden`` and ``state: deleted`` without
  config): a physical Ethernet whose ``alias`` is non-empty is skipped when ``deleteReason`` is not
  ``None``. The decision cannot be taken without the datum, so an absent key refuses during planning,
  before any request is sent.
* ``dcnm_intf_get_diff_deleted`` breakout: ``deletable`` decides; ``deleteReason`` only describes the
  skipped item.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import types
from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

from . import gie_withdrawal_harness as H

DcnmIntf = dcnm_interface.DcnmIntf
ABSENT = object()  # the key is not in the entry at all (synthetic)
NOT_PROVIDED = "not provided by controller"


# ------------------------------------------------------------------ reader
def _summary(**kw):
    item = {
        "ifName": "Ethernet1/1", "serialNo": "SN1", "fabricName": "F", "ifType": "INTERFACE_ETHERNET",
        "isPhysical": "true", "markDeleted": False, "alias": "", "deleteReason": None,
        "complianceStatus": "In-Sync", "underlayPolicies": [],
    }
    for key, value in kw.items():
        if value is ABSENT:
            item.pop(key)
        else:
            item[key] = value
    return item


def _reader_stub():
    s = types.SimpleNamespace()
    s.have_all = []
    s.have_all_cached_snos = set()
    s.have_all_failed_snos = {"SN1"}  # stale failure from a previous read: a good read must clear it
    s.paths = {"IF_DETAIL_WITH_SNO": "/detail?serialNumber={0}"}
    s.ip_sn = {"192.0.2.1": "SN1"}
    s.vpc_ip_sn = {}
    s.module = mock.Mock()
    s._dcnm_intf_authority_key = DcnmIntf._dcnm_intf_authority_key
    s._dcnm_intf_query_serial = DcnmIntf._dcnm_intf_query_serial
    s._dcnm_intf_serial_parts = DcnmIntf._dcnm_intf_serial_parts
    s._dcnm_intf_summary_authorities = lambda sno: set()
    s._dcnm_intf_get_with_retries = mock.Mock()
    return s


def _read(items):
    s = _reader_stub()
    s._dcnm_intf_get_with_retries.return_value = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": items}
    with mock.patch.object(dcnm_interface, "read_reason_note") as note, mock.patch.object(dcnm_interface, "read_reason_clear"):
        ok = DcnmIntf.dcnm_intf_get_have_all_with_sno(s, "SN1")
    return s, ok, note


@pytest.mark.parametrize("value", [ABSENT, None, "", "reason text"], ids=["absent-SYNTHETIC", "null", "empty", "text"])
def test_reader_accepts_every_form_of_deleteReason_and_clears_stale_failure(value):
    item = _summary(deleteReason=value)
    s, ok, note = _read([item])
    assert ok is True
    assert note.call_count == 0
    assert s.have_all_failed_snos == set()
    assert s.have_all_cached_snos
    # the readback is stored as received: no deleteReason=null is invented for an absent key
    assert ("deleteReason" in s.have_all[0]) is (value is not ABSENT)
    if value is not ABSENT:
        assert s.have_all[0]["deleteReason"] == value


@pytest.mark.parametrize("missing", ["fabricName", "ifType", "isPhysical", "markDeleted", "alias", "complianceStatus", "underlayPolicies"])
def test_reader_still_rejects_every_other_missing_field(missing):
    s, ok, note = _read([_summary(deleteReason=ABSENT, **{missing: ABSENT})])
    assert ok is False
    assert s.have_all == [] and s.have_all_failed_snos == {"SN1"}
    assert note.call_args[0][3] == "entry 0: field {0} missing{1}".format(
        missing, " or empty" if missing in ("fabricName", "ifType", "complianceStatus") else "")


def test_absent_deleteReason_does_not_hide_another_defect_in_the_same_entry():
    s, ok, note = _read([_summary(deleteReason=ABSENT, serialNo="")])
    assert ok is False and s.have_all_failed_snos == {"SN1"}
    assert "serialNo" in note.call_args[0][3]


# ------------------------------------------------------------------ overridden / deleted-without-config through main()
SN = H.SERIAL


def _entry(name, alias="", reason=ABSENT, physical="true", if_type="INTERFACE_ETHERNET", **kw):
    item = {
        "ifName": name, "serialNo": SN, "fabricName": H.FABRIC, "ifType": if_type, "isPhysical": physical,
        "markDeleted": False, "alias": alias, "complianceStatus": "In-Sync", "underlayPolicies": [],
        "deletable": True, "mgmtIpAddress": H.SWITCH_IP, "interfaceDbId": 1,
    }
    if reason is not ABSENT:
        item["deleteReason"] = reason
    item.update(kw)
    return item


def _drive(entries, state, configs, have=None):
    """Real main() with interface/detail answering ``entries``; returns (result, calls) from OUR recording transport."""
    calls = []
    base = H._transport(calls, have or [])

    def send(mod, method, path, payload=None):
        response = base(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and "serialNumber=" in path:
            return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": copy.deepcopy(entries)}
        return response

    with mock.patch.object(H, "_transport", lambda _calls, _have: send):
        result, _unused = H.run_configs(configs, state, have=have)
    return result, calls


def _run(entries, state, configs=None):
    return _drive(entries, state, [] if configs is None else configs)


def _mutating(calls):
    return [c for c in calls if c["method"] != "GET"]


STATES = ["overridden", "deleted"]  # `deleted` without config reaches the same sweep


def _have_with_policy(*names):
    """Interfaces carrying a non-default policy, so that reaching the reset decision produces a real modify."""
    out = []
    for name in names:
        out.extend(H.have_for([name], H.TRUNK, None, None))
    return out


def _sweep(entries, state, *names):
    return _drive(entries, state, [], _have_with_policy(*names))


def _resets(calls):
    return [c for c in _mutating(calls) if c["path"].endswith("/interface/modify")]


@pytest.mark.parametrize("state", STATES)
def test_alias_set_and_deleteReason_absent_refuses_by_identity_before_any_write_SYNTHETIC(state):
    result, calls = _sweep([_entry("Ethernet1/9", alias="uplink-a")], state, "Ethernet1/9")
    assert result["failed"] is True
    msg = result["msg"]
    assert "Ethernet1/9" in msg and SN in msg and "deleteReason" in msg and "alias" in msg
    assert _mutating(calls) == [], "the refusal must precede every write"


@pytest.mark.parametrize("state", STATES)
def test_alias_set_and_deleteReason_null_still_resets_like_before(state):
    result, calls = _sweep([_entry("Ethernet1/9", alias="uplink-a", reason=None)], state, "Ethernet1/9")
    assert not result.get("failed"), result.get("msg")
    assert len(_resets(calls)) == 1 and result["diff"][0]["skipped"] == []


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("reason", ["controller text"])
def test_alias_set_and_deleteReason_text_still_skips_like_before(state, reason):
    result, calls = _sweep([_entry("Ethernet1/9", alias="uplink-a", reason=reason)], state, "Ethernet1/9")
    assert not result.get("failed"), result.get("msg")
    assert _mutating(calls) == []
    assert result["diff"][0]["skipped"] == [{"Name": "Ethernet1/9", "Alias": "uplink-a", "Delete Reason": reason}]


@pytest.mark.parametrize("state", STATES)
def test_alias_empty_does_not_consume_deleteReason_and_resets_SYNTHETIC(state):
    result, calls = _sweep([_entry("Ethernet1/9", alias="", reason=ABSENT)], state, "Ethernet1/9")
    assert not result.get("failed"), result.get("msg")
    assert len(_resets(calls)) == 1


@pytest.mark.parametrize("state", STATES)
def test_mixed_switch_absent_datum_does_not_disqualify_the_switch_SYNTHETIC(state):
    # Without the interface that needs the datum, the same switch with absent keys elsewhere is swept normally.
    entries = [_entry("Ethernet1/1", alias=""), _entry("mgmt0", if_type="INTERFACE_MGMT", physical="false")]
    result, calls = _sweep(entries, state, "Ethernet1/1")
    assert not result.get("failed"), result.get("msg")
    assert "could not be read authoritatively" not in str(result.get("msg", ""))
    assert len(_resets(calls)) == 1


@pytest.mark.parametrize("state", STATES)
def test_mixed_switch_refuses_the_mutation_that_needs_the_datum_and_names_only_that_interface_SYNTHETIC(state):
    entries = [_entry("Ethernet1/1", alias=""), _entry("mgmt0", if_type="INTERFACE_MGMT", physical="false"),
               _entry("Ethernet1/9", alias="uplink-a")]
    result, calls = _sweep(entries, state, "Ethernet1/1", "Ethernet1/9")
    assert result["failed"] is True and "Ethernet1/9" in result["msg"] and "Ethernet1/1 " not in result["msg"]
    assert "could not be read authoritatively" not in result["msg"]
    assert _mutating(calls) == [], "planning refuses before the reset of the interface that did not need the datum is sent"


def test_interface_excluded_by_override_types_is_not_invalidated_by_absence_SYNTHETIC():
    # alias set and key absent, but the sweep is restricted to another type: the decision is never reached.
    # Driven through the real sweep with the authority-scope stub (the module params are not exposed by main() harness).
    from . import test_dcnm_intf_override_authority_scope as A

    have = A._have("Ethernet1/9", "INTERFACE_ETHERNET", is_physical="true")
    have["alias"] = "uplink-a"
    del have["deleteReason"]  # the key is absent, not null
    stub = A._stub([have])
    stub.intf_detail_fetch_failed_snos = set()
    stub.intf_detail_cached_snos = {A.SERIAL}
    stub.module.params["override_intf_types"] = ["INTERFACE_PORT_CHANNEL"]
    A._run(stub)
    assert stub.module.fail_json.call_count == 0

    # control: the same entry is refused when Ethernet is in scope, so the exclusion is what protected it
    stub = A._stub([dict(have)])
    stub.intf_detail_fetch_failed_snos = set()
    stub.intf_detail_cached_snos = {A.SERIAL}
    stub.module.params["override_intf_types"] = []
    stub.module.fail_json.side_effect = A._FailJson
    with pytest.raises(A._FailJson):
        A._run(stub)
    assert "Ethernet1/9" in stub.module.fail_json.call_args.kwargs["msg"]


# ------------------------------------------------------------------ breakout deleted
def _run_breakout(entry):
    conf = {"name": "Ethernet1/1", "type": "breakout", "switch": [H.SWITCH_IP]}
    return _drive([entry], "deleted", [conf])


def _sub(reason, deletable):
    return _entry("Ethernet1/1/1", alias="x", reason=reason, deletable=deletable)


def test_breakout_non_deletable_absent_key_skips_with_neutral_reason_SYNTHETIC():
    result, calls = _run_breakout(_sub(ABSENT, False))
    assert not result.get("failed"), result.get("msg")
    skipped = result["diff"][0]["skipped"]
    assert skipped[0]["Name"] == "Ethernet1/1/1" and skipped[0]["Delete Reason"] == NOT_PROVIDED
    assert _mutating(calls) == []


@pytest.mark.parametrize("reason,shown", [(None, None), ("held by policy", "held by policy")], ids=["null", "text"])
def test_breakout_non_deletable_present_field_keeps_previous_representation(reason, shown):
    result, calls = _run_breakout(_sub(reason, False))
    skipped = result["diff"][0]["skipped"]
    assert skipped[0]["Delete Reason"] == shown
    assert _mutating(calls) == []


@pytest.mark.parametrize("reason", [ABSENT, None, "text"], ids=["absent-SYNTHETIC", "null", "text"])
def test_breakout_deletable_is_decided_by_deletable_alone(reason):
    result, calls = _run_breakout(_sub(reason, True))
    assert not result.get("failed"), result.get("msg")
    assert result["diff"][0]["skipped"] == []
    assert any("breakout" in c["path"].lower() for c in _mutating(calls)), "a deletable breakout is still removed"
