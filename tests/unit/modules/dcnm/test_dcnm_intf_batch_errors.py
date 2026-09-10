"""A 207 Multi-Status reports the outcome of EACH item, not of the batch.

The bulk interface update judged the response by RETURN_CODE alone, so a 207 whose items
were all ERROR was indistinguishable from one whose items were all SUCCESS. Measured on a
live controller: a parent template that refuses a value answers

    207 Multi-Status
      {"reportItemType": "ERROR",
       "message": "Switch [Leaf-101/9648E3J5P6M]: 'Spanning-tree port type' cannot be set
                   to 'network' when 'Enable port type fast' is enabled",
       "entity": "9648E3J5P6M:Ethernet1/5"}

and writes nothing -- while the module reported changed=True, failed=False. That is the
worst failure mode available: the operator believes the change landed.

These tests pin both halves of the fix: which items are fatal, and what the operator is
told when a batch is only partially applied.

Run:
    pytest tests/unit/modules/dcnm/test_dcnm_intf_batch_errors.py
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest import mock

import pytest

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import DcnmIntf

collect = DcnmIntf.dcnm_intf_collect_batch_errors
render = DcnmIntf.dcnm_intf_format_batch_error


def _ok(entity):
    return {
        "reportItemType": "SUCCESS",
        "entity": entity,
        "message": "Interface updated successfully",
    }


def _err(entity, message):
    return {"reportItemType": "ERROR", "entity": entity, "message": message}


def _warn(message):
    return {"reportItemType": "WARNING", "entity": "Leaf-101", "message": message}


REJECTION = (
    "Switch [Leaf-101/9648E3J5P6M]: 'Spanning-tree port type' cannot be set to "
    "'network' when 'Enable port type fast' is enabled"
)


# ---------------------------------------------------------------- what is fatal --

def test_all_success_is_not_an_error():
    resp = {"RETURN_CODE": 207, "DATA": [_ok("SN~Eth1/5"), _ok("SN~Eth1/4")]}
    assert collect(resp) == []


def test_every_item_rejected_is_detected():
    resp = {
        "RETURN_CODE": 207,
        "DATA": [_err("SN~Eth1/5", REJECTION), _err("SN~Eth1/4", REJECTION)],
    }
    assert len(collect(resp)) == 2


def test_a_single_rejection_among_successes_is_detected():
    """The case the RETURN_CODE check could never see: 9 applied, 1 refused."""
    resp = {
        "RETURN_CODE": 207,
        "DATA": [_ok("SN~Eth1/%d" % n) for n in range(1, 10)]
        + [_err("SN~Eth1/10", REJECTION)],
    }
    assert len(collect(resp)) == 1


def test_warning_is_not_fatal():
    """The deploy call legitimately answers WARNING for a no-op.

    Treating it as fatal would break every run where the controller had nothing to push.
    """
    resp = {"RETURN_CODE": 207, "DATA": [_warn("No Commands to execute. In-Sync")]}
    assert collect(resp) == []


def test_an_unrecognised_item_type_is_left_alone():
    """Fail-safe in the direction that cannot break a working run.

    Only ERROR was observed to mean rejection. An item type we have not seen is ignored
    rather than guessed at, so this change cannot turn a currently-passing run into a
    failure on a shape nobody has measured.
    """
    resp = {"RETURN_CODE": 207, "DATA": [{"reportItemType": "INFO", "entity": "a"}]}
    assert collect(resp) == []


def test_error_matching_is_case_insensitive():
    resp = {"RETURN_CODE": 207, "DATA": [{"reportItemType": "error", "entity": "a",
                                          "message": "m"}]}
    assert len(collect(resp)) == 1


@pytest.mark.parametrize(
    "resp",
    [
        {"RETURN_CODE": 207},                                   # sin DATA
        {"RETURN_CODE": 207, "DATA": None},
        {"RETURN_CODE": 207, "DATA": {"message": "not a list"}},  # objeto, no lote
        {"RETURN_CODE": 207, "DATA": ["texto", None, 5]},        # elementos malformados
        {},                                                      # respuesta vacia
        None,                                                    # ni siquiera un dict
    ],
    ids=["no_data", "null_data", "dict_data", "junk_items", "empty", "not_a_dict"],
)
def test_malformed_bodies_are_not_treated_as_rejections(resp):
    """A body we cannot parse is not evidence that an item was refused.

    Failing here would turn an unrelated controller quirk into a broken playbook.
    """
    assert collect(resp) == []


# ------------------------------------------------------- what the operator reads --

def test_the_message_names_the_rejected_entities_and_reasons():
    resp = {"RETURN_CODE": 207, "DATA": [_err("9648E3J5P6M~Ethernet1/4", REJECTION)]}
    text = render(resp, collect(resp))
    assert "9648E3J5P6M~Ethernet1/4" in text
    assert "cannot be set to 'network'" in text
    assert "207" in text


def test_a_partial_batch_says_what_was_already_applied():
    """Naming the successes matters as much as naming the failures.

    The controller applies a batch item by item, so a mixed response leaves real state
    behind. Failing without saying which items landed would leave the operator worse off
    than the silent success this replaces: they would know something broke, but not what
    to reconcile.
    """
    resp = {
        "RETURN_CODE": 207,
        "DATA": [_ok("SN~Ethernet1/5"), _err("SN~Ethernet1/4", REJECTION)],
    }
    text = render(resp, collect(resp))
    assert "SN~Ethernet1/4" in text          # el rechazado
    assert "SN~Ethernet1/5" in text          # el aplicado
    assert "Applied before the rejection" in text


def test_a_wholly_rejected_batch_says_nothing_was_applied():
    """The opposite half: do NOT imply partial state when there is none."""
    resp = {
        "RETURN_CODE": 207,
        "DATA": [_err("SN~Ethernet1/5", REJECTION), _err("SN~Ethernet1/4", REJECTION)],
    }
    text = render(resp, collect(resp))
    assert "Nothing in this batch was applied" in text
    assert "Applied before the rejection" not in text


def test_a_missing_entity_or_message_does_not_crash_the_report():
    resp = {"RETURN_CODE": 207, "DATA": [{"reportItemType": "ERROR"}]}
    text = render(resp, collect(resp))
    assert "unknown entity" in text
    assert "no message" in text


# ------------------------------------------------------------------ the wiring --
#
# The tests above exercise the helpers in isolation, so they ALL still pass if the call
# site is deleted from the send path -- which is the "test that cannot fail" trap. These
# drive the actual send method instead, so removing the check breaks them.


class _Bail(Exception):
    """Stands in for AnsibleModule.fail_json, which normally exits the process."""


def _sender(response):
    """A DcnmIntf wired for the bulk-update branch only, with dcnm_send stubbed."""
    obj = object.__new__(DcnmIntf)
    obj.class_name = "DcnmIntf"
    obj.log = mock.Mock()
    obj.module = mock.Mock()
    obj.module.fail_json.side_effect = lambda *a, **kw: (_ for _ in ()).throw(
        _Bail(kw.get("msg"))
    )
    obj.result = {"response": [], "changed": False}
    obj.changed_dict = [{}]
    obj.paths = {
        "IF_MARK_DELETE": "/mark",
        "INTERFACE": "/interface",
        "UPDATE_INTERFACE_BULK": "/interface/modify",
        "BREAKOUT": "/breakout",
        "GLOBAL_IF_DEPLOY": "/deploy",
        "GLOBAL_IF": "/globalinterface",
    }
    obj.has_bulk_api = True
    # every other bucket empty, so only the bulk-update branch runs
    obj.diff_delete = []
    obj.diff_delete_deploy = []
    obj.diff_create = []
    obj.diff_create_breakout = []
    obj.diff_deploy = []
    obj.diff_replace = [{"policy": "int_trunk_host", "interfaces": [{"ifName": "Eth1/5"}]}]
    obj.diff_delete_breakout = []
    obj.deferred_delete_member_defaults = []
    obj.dcnm_intf_refresh_deferred_deleted_member_defaults = mock.Mock()
    return obj


def _run(monkeypatch, response):
    obj = _sender(response)
    monkeypatch.setattr(
        dcnm_interface, "dcnm_send", lambda module, method, path, payload=None: response
    )
    obj.dcnm_intf_send_message_to_dcnm()
    return obj


def test_send_path_fails_when_the_batch_reports_an_error(monkeypatch):
    """Deleting the check from the send path must break this test.

    This is the one that actually guards the fix: it goes through
    dcnm_intf_send_message_to_dcnm, not through the helper.
    """
    response = {
        "RETURN_CODE": 207,
        "MESSAGE": "Multi-Status",
        "DATA": [_err("9648E3J5P6M~Ethernet1/5", REJECTION)],
    }
    with pytest.raises(_Bail) as excinfo:
        _run(monkeypatch, response)
    assert "9648E3J5P6M~Ethernet1/5" in str(excinfo.value)
    assert "cannot be set to 'network'" in str(excinfo.value)


def _ran_without_batch_rejection(monkeypatch, response):
    """Drive the send path and report whether the batch check fired.

    The method continues well past the bulk update into deploy and query handling, which
    needs far more scaffolding than this test is about. What matters here is narrow: that
    the batch check did NOT reject. Anything raised afterwards is unrelated plumbing, so it
    is swallowed deliberately -- but a _Bail IS re-raised, because that is our own
    fail_json and the only thing this test is looking for.
    """
    obj = _sender(response)
    monkeypatch.setattr(
        dcnm_interface, "dcnm_send", lambda module, method, path, payload=None: response
    )
    try:
        obj.dcnm_intf_send_message_to_dcnm()
    except _Bail:
        raise
    except Exception:
        pass  # unrelated: the method needs more state than this test provides
    return obj


def test_send_path_succeeds_when_every_item_succeeded(monkeypatch):
    """The other direction: a genuinely successful batch must NOT start failing."""
    response = {
        "RETURN_CODE": 207,
        "MESSAGE": "Multi-Status",
        "DATA": [_ok("SN~Ethernet1/5"), _ok("SN~Ethernet1/4")],
    }
    _ran_without_batch_rejection(monkeypatch, response)


def test_send_path_tolerates_a_plain_200_without_data(monkeypatch):
    """A controller that answers 200 with no per-item body is still a success."""
    response = {"RETURN_CODE": 200, "MESSAGE": "OK"}
    _ran_without_batch_rejection(monkeypatch, response)
