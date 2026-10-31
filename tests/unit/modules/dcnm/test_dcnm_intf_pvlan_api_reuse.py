"""API-REUSE: two read reuses, local to ONE invocation and to the phase BEFORE its first write.

1. PLANNING-REUSE: the saved-state recognition reads ONE forced preview per queried serial and every candidate on that switch judges it;
   the gates keep their own fresh preview. Measured before (d76094b0): a saved mixed Po retry recomputed the same switch 3 times
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


# ================================================================== 2. PREWRITE-REUSE (vPC reads before the first write)
from . import test_dcnm_intf_pvlan_vpc_child_ids as CI  # noqa: E402
from . import test_dcnm_intf_pvlan_vpc_read_diagnostics as RD  # noqa: E402

POLICIES, DETAIL = "/control/policies/switches/", "/rest/interface?serialNumber="


def reads(calls, mark, serial, before=None):
    end = len(calls) if before is None else before
    return sum(1 for c in calls[:end] if c[0] == "GET" and (mark + serial) in c[1] and "&ifName=" not in c[1])


def first_write(calls):
    return next(i for i, c in enumerate(calls) if c[0] in ("POST", "PUT", "DELETE"))


def test_vpc_creation_reads_each_peers_policies_once_before_writing_and_fresh_after_the_deploy():
    """Peers with DIFFERENT port-channel numbers, playbook order reversed (peer1 = SN2): each serial gets its own state."""
    pcids = ("11", "12")
    ctrl = V.baseline_ctrl()
    V.create_previews(ctrl)
    CI.remap(ctrl, pcids)
    # peer1_* of the playbook belong to its FIRST switch (SN2 here): SN2 owns 12 and SN1 owns 11
    status, result = V.run_vpc(ctrl, [V.vpc_item(switches=[V.IP2, V.IP1], peer1_members=[V.M2], peer2_members=[V.M1], peer1_pcid=12,
                                                 peer2_pcid=11)])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    w = first_write(ctrl.calls)
    for serial in (V.SN1, V.SN2):
        assert reads(ctrl.calls, POLICIES, serial, w) == 1, serial      # before: 2 (generic + vPC compare)
        assert reads(ctrl.calls[w:], POLICIES, serial) >= 1, serial     # the post-deploy verification still reads its own
    # each serial kept its own Po number and member (the base result of the swapped creation)
    nv = CI.sent_nv(ctrl)
    assert (nv["PEER1_PCID"], nv["PEER2_PCID"]) == ("11", "12") and nv["PEER1_MEMBER_INTERFACES"] == V.M1
    assert "port-channel11" in ctrl.nodes[V.SN1] and "port-channel12" in ctrl.nodes[V.SN2]


def test_a_failed_generic_policy_read_is_not_reused_the_vpc_reader_reads_again_and_judges_it():
    """SN2's generic policy read fails once: nothing is recorded, the vPC reader reads SN2 again (fresh) and the creation proceeds;
    SN1's complete read is still reused. A failed read is never taken as an empty policy list."""

    class OnceFailing(RD.CanaryController):
        def __call__(self, mod, method, path, data=None):
            if POLICIES + V.SN2 in path and not getattr(self, "failed_once", False):
                self.failed_once = True
                self.calls.append((method, path, data))
                return {"RETURN_CODE": 500, "MESSAGE": "x", "DATA": {}}
            return super(OnceFailing, self).__call__(mod, method, path, data)

    ctrl = OnceFailing().seed_baseline()
    V.create_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    w = first_write(ctrl.calls) if status == "exit" else len(ctrl.calls)
    assert reads(ctrl.calls, POLICIES, V.SN2, w) >= 2, "the failed generic read was not reused as a state"
    assert reads(ctrl.calls, POLICIES, V.SN1, w) == 1


def test_a_policy_read_failing_for_the_vpc_reader_as_well_still_refuses_with_its_peer_named():
    """Both reads of SN2's policies fail: the existing refusal (peer and stage named, nothing written) is unchanged."""
    ctrl = RD.CanaryController().seed_baseline()
    ctrl.canary_failures.add(POLICIES + V.SN2)
    got = RD.refused(ctrl)
    assert any(V.SN2 in l and "switch policy list" in l for l in got), got
    assert not any(V.SN1 in l and "switch policy list" in l for l in got), got


def test_an_unchanged_vpc_repeat_still_reads_and_writes_nothing():
    pcids = ("11", "12")
    ctrl = CI.seeded(pcids)
    V.converged_previews(ctrl)
    CI.remap(ctrl, pcids)
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_pcid=11, peer2_pcid=12)])
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")
    for serial in (V.SN1, V.SN2):
        assert reads(ctrl.calls, POLICIES, serial) == 1, serial          # before: 2
        assert reads(ctrl.calls, "config-preview/", serial) == 1, serial  # the prior gate keeps its fresh preview


def test_a_description_update_keeps_its_modify_and_deploy_and_both_peers_new_text():
    pcids = ("11", "12")
    ctrl = CI.seeded(pcids, descs=("base-a", "base-b"))
    ctrl.vpc_previews[V.SN1] = [V.converged_preview(V.SN1, V.M1, desc="base-a"), V.description_preview(V.SN1, V.M1, "base-a", "new-a")]
    ctrl.vpc_previews[V.SN2] = [V.converged_preview(V.SN2, V.M2, desc="base-b"), V.description_preview(V.SN2, V.M2, "base-b", "new-b")]
    CI.remap(ctrl, pcids)
    status, result = V.run_vpc(ctrl, [V.vpc_item(peer1_pcid=11, peer2_pcid=12, peer1_description="new-a", peer2_description="new-b")],
                               state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    assert ctrl.nodes[V.SN1]["port-channel11"]["nvPairs"]["DESC"] == "new-a" and ctrl.nodes[V.SN2]["port-channel12"]["nvPairs"]["DESC"] == "new-b"


class _ReuseObj(object):
    def __init__(self):
        self.have_all_cached_snos, self.have_all_failed_snos = set(), set()
        self.intf_detail_cached_snos, self.intf_detail_fetch_failed_snos = set(), set()

    @staticmethod
    def _dcnm_intf_authority_key(serial):
        return serial


def test_prewrite_records_are_per_physical_serial_dropped_on_failure_and_closed_by_sending():
    obj = _ReuseObj()
    module.pvlan_prewrite_note(obj, "policies", "SNA", True, [{"x": 1}])
    module.pvlan_prewrite_note(obj, "policies", "SNA~SNB", True, [{"x": 2}])   # a pair read is never recorded
    assert module.pvlan_prewrite_reusable(obj, "policies", "SNA") and not module.pvlan_prewrite_reusable(obj, "policies", "SNB")
    assert not module.pvlan_prewrite_reusable(obj, "policies", "SNA~SNB")
    module.pvlan_prewrite_note(obj, "policies", "SNA", False)                  # a later failed read drops the earlier one
    assert not module.pvlan_prewrite_reusable(obj, "policies", "SNA")
    module.pvlan_prewrite_note(obj, "detail", "SNA", True)
    assert not module.pvlan_prewrite_reusable(obj, "detail", "SNA"), "detail needs the serial still cached as authoritative"
    obj.intf_detail_cached_snos.add("SNA")
    assert module.pvlan_prewrite_reusable(obj, "detail", "SNA")
    obj.intf_detail_fetch_failed_snos.add("SNA")
    assert not module.pvlan_prewrite_reusable(obj, "detail", "SNA")
    obj.intf_detail_fetch_failed_snos.clear()
    obj._pvlan_sending = True
    assert not module.pvlan_prewrite_reusable(obj, "detail", "SNA")
    module.pvlan_prewrite_note(obj, "policies", "SNC", True, [])               # nothing is recorded once sending started
    obj._pvlan_sending = False
    assert not module.pvlan_prewrite_reusable(obj, "policies", "SNC")


def test_the_summary_is_always_read_again_by_the_vpc_reader():
    """Not reused on purpose: the generic summary of the OTHER peer rewrites this serial's have_all entries (pair union), so the
    pre-write summary of a serial is not provably complete when the vPC reader runs."""
    import inspect
    src = inspect.getsource(module.DcnmIntf.dcnm_intf_pvlan_vpc_read_serial)
    assert "if self.dcnm_intf_get_have_all_with_sno(serial):" in src and 'pvlan_prewrite_reusable(self, "summary"' not in src
