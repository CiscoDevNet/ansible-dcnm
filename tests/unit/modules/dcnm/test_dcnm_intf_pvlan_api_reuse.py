"""API-REUSE (Kapa, PR725 night closure): two read reuses, local to ONE invocation and to the phase BEFORE its first write.

1. PLANNING-REUSE: the saved-state recognition reads ONE forced preview per queried serial and every candidate on that switch judges it;
   the gates keep their own fresh preview. Measured before (G8 d76094b0): a saved mixed Po retry recomputed the same switch 3 times
   before its gate (4 previews in all).
2. PREWRITE-REUSE: see the second section.

Real main() through the existing harnesses; only the controller boundary is faked. Results, deploy payloads and saved-state records are
asserted to stay those of the base, not only the counters.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
from unittest.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from . import test_dcnm_intf_pvlan_mixed_saved_retry as SR
from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import SERIAL, preview

PREVIEW = "/config-preview/"


def previews_by_serial(calls):
    out = {}
    for c in calls:
        if c[0] == "GET" and PREVIEW in c[1]:
            serial = c[1].split(PREVIEW)[1].split("?")[0]
            out[serial] = out.get(serial, 0) + 1
    return out


# ================================================================== 1. PLANNING-REUSE, end to end
def test_saved_mixed_po_retry_reads_one_planning_preview_and_one_gate_preview_with_the_same_outcome():
    ctrl = SR.saved_po_ctrl()
    SR.stage(ctrl)
    status, result, start = SR.retry(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    # before: 4 (Po301 candidate, po502 candidate, conventional sibling, gate); now 1 planning + 1 gate
    assert previews_by_serial(ctrl.calls[start:]) == {SERIAL: 2}
    # the outcome is the base one: one deploy of exactly the two saved aggregates, no mark-delete, both completions reported
    bodies = SR.deploy_bodies(ctrl, start)
    assert len(bodies) == 1 and sorted(i["ifName"].lower() for i in bodies[0]) == ["port-channel301", "port-channel502"]
    assert "interface/markdelete" not in SR.later_writes(ctrl, start)
    assert ctrl.conv_marked is None and ctrl.marked is None, "both port-channels are gone after the deploy"
    rel = [r for r in result["pvlan_gate_invocation_releases"] if r["site"] == "delete_deploy"]
    assert rel == [{"site": "delete_deploy", "serial": SERIAL, "interfaces": ["ethernet1/14"], "withdrawn": ["no interface port-channel301"]}]
    # the base records (d76094b0): the PVLAN Po continuation and the conventional sibling, both completing the saved deletion
    assert [(r.get("kind"), r.get("name"), r.get("operation"), r.get("state")) for r in result["pvlan_saved"]] == [
        (None, None, "delete", "completing the saved deletion"),
        ("conventional", "Port-channel301", "delete", "completing the saved deletion")], result["pvlan_saved"]


def test_saved_mixed_vpc_retry_reads_each_peers_own_planning_preview_once():
    ctrl = SR.saved_vpc_ctrl()
    status, result, start = SR.vpc_retry(ctrl)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    counts = previews_by_serial(ctrl.calls[start:])
    assert set(counts) == {V.SN1, V.SN2}, counts
    assert counts[V.SN1] == counts[V.SN2] == 2, counts  # 1 planning + 1 gate per peer (before: 3 per peer)
    sent = sorted((i["serialNumber"], i["ifName"].lower()) for i in json.loads(ctrl.deploys()[0][2]))
    assert sent == [(V.PAIR, "vpc10"), (V.PAIR, "vpc305")]
    assert SR.vpc_owned(result) == [(V.SN1, ("ethernet1/5",), ("no interface port-channel305",)),
                                    (V.SN2, ("ethernet1/6",), ("no interface port-channel305",))]


def test_a_new_process_reads_its_own_planning_preview_nothing_is_carried_over():
    ctrl = SR.saved_po_ctrl()
    SR.stage(ctrl)
    staged = len(ctrl.calls)
    _status, _result, start = SR.retry(ctrl)
    assert start == staged and previews_by_serial(ctrl.calls[start:]) == {SERIAL: 2}


# ================================================================== 1. PLANNING-REUSE, the helper's contract
class _Obj(object):
    """The smallest object the helper needs; the method under test is the module's own."""

    def __init__(self):
        self.module = object()
        self.fabric = "f"
        self.paths = {"PVLAN_CONFIG_PREVIEW": "/control/fabrics/{}/config-preview/{}?forceShowRun=true"}

    def planning(self, query_serial):
        return module.DcnmIntf.dcnm_intf_pvlan_planning_preview(self, query_serial)


def _run_helper(answers, calls):
    def fake(mod, method, path, data=None):
        calls.append(path)
        return answers.pop(0)
    return patch.object(module, "dcnm_send", side_effect=fake)


GOOD_A = preview(["interface ethernet1/9", "  description x"], serial="SNA")
GOOD_B = preview([], serial="SNB")
BAD = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}


def test_an_unreadable_preview_is_returned_to_its_caller_and_never_reused_as_a_state():
    obj, calls = _Obj(), []
    with _run_helper([BAD, GOOD_A], calls):
        assert obj.planning("SNA") is BAD          # the caller judges the failure as before
        assert obj.planning("SNA") is GOOD_A       # read again: the failure was not cached
        assert obj.planning("SNA") is GOOD_A       # now reused
    assert len(calls) == 2


def test_each_queried_serial_has_its_own_answer():
    obj, calls = _Obj(), []
    with _run_helper([GOOD_A, GOOD_B], calls):
        assert obj.planning("SNA") is GOOD_A and obj.planning("SNB") is GOOD_B
        assert obj.planning("SNA") is GOOD_A and obj.planning("SNB") is GOOD_B
    assert [c.split(PREVIEW)[1].split("?")[0] for c in calls] == ["SNA", "SNB"]


def test_an_answer_of_another_serial_is_not_kept_for_the_queried_one():
    obj, calls = _Obj(), []
    with _run_helper([GOOD_B, GOOD_A], calls):
        assert obj.planning("SNA") is GOOD_B   # returned as read (its caller refuses it), not cached under SNA
        assert obj.planning("SNA") is GOOD_A
    assert len(calls) == 2


def test_once_sending_starts_every_read_is_fresh():
    obj, calls = _Obj(), []
    with _run_helper([GOOD_A, GOOD_A, GOOD_A], calls):
        obj.planning("SNA")
        obj._pvlan_sending = True
        obj.planning("SNA")
        obj.planning("SNA")
    assert len(calls) == 3


def test_the_sender_closes_the_planning_phase_before_any_request():
    """Static: the sending entry point marks the phase and drops the planning answers before its first request."""
    import inspect
    src = inspect.getsource(module.DcnmIntf.dcnm_intf_send_message_to_dcnm)
    first_request = min(i for i in (src.find("dcnm_send("), src.find("resp = dcnm_send")) if i >= 0)
    assert 0 <= src.find("self._pvlan_sending = True") < first_request
    assert 0 <= src.find('pop("pvlan_planning_previews", None)') < first_request
