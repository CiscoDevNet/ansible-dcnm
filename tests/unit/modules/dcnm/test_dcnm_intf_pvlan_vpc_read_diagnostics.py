"""vPC PVLAN creation / member join refused on an unreadable peer: the refusal names the peer, the read stage and a controlled reason.

NOT LIVE TESTED. Real main() through the existing vPC harness (test_dcnm_intf_pvlan_vpc_harness: VpcController + run_vpc) and the
membership double of test_dcnm_intf_pvlan_member_updates; one trigger per case at the external boundary. Every refusal keeps zero
mutating requests for the whole invocation; the general refusal lines are kept; the cause appears once per peer and stage. Reasons are
controlled text (status number, field name, entry index, failure category): a fake canary placed in failing responses never appears.
The earlier, separate refusal of a total detail failure on the pair's FIRST serial (read before this preflight) is not changed here.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import hashlib
import json

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

from . import test_dcnm_intf_pvlan_member_updates as MU
from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_harness import TRUNK, trunk_host_nv

SN1, SN2, M1, M2 = V.SN1, V.SN2, V.M1, V.M2
SUMMARY, BULK, POLICIES = "/rest/interface/detail?serialNumber=", "/rest/interface?serialNumber=", "/control/policies/switches/"
ABSENT = "the absence of the port-channel and of the vPC children could not be established authoritatively"
UNREAD = "its current state could not be read authoritatively"
CANARY = "SYNTH-CANARY-Zq9"  # fake sensitive-looking value placed inside failing responses; it must never reach the error


def mutating(ctrl):
    return [(m, p) for m, p, _d in ctrl.calls if m in ("POST", "PUT", "DELETE")]


def lines(result):
    return [l.strip() for l in result.get("msg", "").splitlines() if l.startswith("  ")]


def cause(serial, stage, reason):
    return "{0} on {1}: {2} {1} could not be read authoritatively ({3})".format(V.VPC, serial, stage, reason)


def refused(ctrl, items=None):
    status, result = V.run_vpc(ctrl, items or [V.vpc_item()])
    assert status == "fail", result
    assert mutating(ctrl) == [], mutating(ctrl)
    assert result["msg"].endswith("No configuration or deployment request was sent.")
    assert CANARY not in json.dumps(result)
    return lines(result)


def generic(serial, member):
    """The two general lines (kept). The member label is the module's resolved spelling (controller spelling when the bulk detail was
    read, the playbook spelling otherwise), so these two lines are compared case-insensitively; cause lines are compared exactly."""
    return {("{0} on {1}: {2}".format(V.VPC, serial, ABSENT)).lower(), ("{0} on {1}: {2}".format(member, serial, UNREAD)).lower()}


def folded(got):
    return {l.lower() for l in got}


class CanaryController(V.VpcController):
    """VpcController whose failing answers carry a fake canary in every place a careless diagnostic could copy from."""

    def __init__(self):
        super(CanaryController, self).__init__()
        self.canary_failures = set()

    def __call__(self, mod, method, path, data=None):
        for mark in self.canary_failures:
            if mark in path:
                self.calls.append((method, path, data))
                return {"RETURN_CODE": 500, "MESSAGE": CANARY, "DATA": {"message": CANARY, "detail": CANARY}}
        return super(CanaryController, self).__call__(mod, method, path, data)


# ------------------------------------------------------------------ positive control: unchanged requests and payloads
def test_coherent_creation_keeps_its_exact_request_sequence_and_payloads():
    ctrl = V.baseline_ctrl()
    V.create_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is True, result
    calls = [(m, p.split("/appcenter/cisco/ndfc/api/v1/lan-fabric")[-1]) for m, p, _d in ctrl.calls]
    writes = [d for m, _p, d in ctrl.calls if m in ("POST", "PUT", "DELETE")]
    # measured on the unmodified base 3bfa68cb with the same double: 26 calls, create + deploy (unchanged through d76094b0).
    # PREWRITE-REUSE: the pre-write vPC compare reuses this invocation's own complete generic reads of the same physical serial:
    # the policy list of FDO00000001 and FDO00000002 and the bulk detail of FDO00000002 are no longer read twice -> 23 calls.
    # The writes (create + deploy payloads) are byte-identical to the base.
    assert len(calls) == 23
    assert hashlib.sha256(json.dumps(calls).encode()).hexdigest()[:16] == "052300081d2ad0bf"
    assert hashlib.sha256(json.dumps(writes).encode()).hexdigest()[:16] == "9482b18d85c7f831"


# ------------------------------------------------------------------ creation: each read stage, one peer, peer isolation
def test_summary_http_status_names_peer_stage_and_status_only_for_that_peer():
    ctrl = CanaryController().seed_baseline()
    ctrl.canary_failures.add(SUMMARY + SN1)
    got = refused(ctrl)
    assert generic(SN1, M1) <= folded(got)
    assert cause(SN1, "the interface summary of", "HTTP 500 after 3 attempt(s)") in got
    assert not any(SN2 in l for l in got)


def test_summary_entry_without_markDeleted_on_a_foreign_port_names_the_entry_and_field():
    ctrl = V.baseline_ctrl()
    ctrl.nodes[SN1]["Ethernet1/40"] = {"policy": TRUNK, "nvPairs": trunk_host_nv("Ethernet1/40")}
    orig = ctrl._peer_summary

    def summary(serial):
        out = orig(serial)
        for e in out:
            if serial == SN1 and e["ifName"] == "Ethernet1/40":
                e.pop("markDeleted")
                e["alias"] = CANARY
        return out

    ctrl._peer_summary = summary
    got = refused(ctrl)
    assert generic(SN1, M1) <= folded(got)
    assert cause(SN1, "the interface summary of", "entry 0: field markDeleted missing") in got


def test_bulk_record_without_nvPairs_names_the_record_once_per_peer():
    ctrl = V.baseline_ctrl()
    orig = ctrl._peer_details

    def details(serial):
        out = orig(serial)
        if serial == SN2:
            out.append({"policy": "int_trunk_host", "interfaces": [{"serialNumber": SN2, "ifName": "Ethernet1/42", "note": CANARY}]})
        return out

    ctrl._peer_details = details
    got = refused(ctrl)
    detail = [l for l in got if "the interface detail of" in l]
    assert detail == [cause(SN2, "the interface detail of", "record 1.0 lacks the nvPairs object")], detail
    assert generic(SN2, M2) <= folded(got) and not any(SN1 in l for l in got)


def test_bulk_duplicate_record_is_named():
    ctrl = V.baseline_ctrl()
    orig = ctrl._peer_details

    def details(serial):
        out = orig(serial)
        if serial == SN2:
            dup = copy.deepcopy(out[0])
            dup["interfaces"][0]["nvPairs"]["DESC"] = CANARY
            out.append(dup)
        return out

    ctrl._peer_details = details
    got = refused(ctrl)
    assert cause(SN2, "the interface detail of", "record 1.0 duplicates an earlier record of the same interface") in got


def test_bulk_http_status_on_the_second_peer():
    ctrl = CanaryController().seed_baseline()
    ctrl.canary_failures.add(BULK + SN2)
    got = refused(ctrl)
    assert generic(SN2, M2) <= folded(got)
    assert cause(SN2, "the interface detail of", "HTTP 500 after 3 attempt(s)") in got


def test_policy_list_invalid_element_on_both_peers():
    ctrl = V.baseline_ctrl()
    ctrl.policies_override = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [CANARY]}
    got = refused(ctrl)
    for serial, member in ((SN1, M1), (SN2, M2)):
        assert generic(serial, member) <= folded(got)
        assert cause(serial, "the switch policy list of", "element 0 is not an object") in got


def test_policy_list_http_status_is_a_single_attempt():
    ctrl = CanaryController().seed_baseline()
    ctrl.canary_failures.add(POLICIES + SN1)
    got = refused(ctrl)
    assert cause(SN1, "the switch policy list of", "HTTP 500 after 1 attempt(s)") in got


def test_summary_failure_on_both_peers_names_both():
    ctrl = V.baseline_ctrl()
    ctrl.read_failures.update({SUMMARY + SN1, SUMMARY + SN2})
    got = refused(ctrl)
    for serial, member in ((SN1, M1), (SN2, M2)):
        assert generic(serial, member) <= folded(got)
        assert cause(serial, "the interface summary of", "HTTP 500 after 3 attempt(s)") in got
    assert len(got) == 6


def test_exhausted_read_budget_says_no_request_was_sent_and_keeps_the_last_real_failure():
    ctrl = V.baseline_ctrl()
    extra = "Ethernet1/9"
    nv = trunk_host_nv(extra)
    nv["ADMIN_STATE"] = "false"
    ctrl.nodes[SN2][extra] = {"policy": TRUNK, "nvPairs": nv}
    ctrl.read_failures.add(BULK + SN2)
    got = refused(ctrl, [V.vpc_item(peer2_members=[M2, extra])])
    detail = [l for l in got if "the interface detail of" in l]
    assert detail == [cause(SN2, "the interface detail of",
                            "read skipped: the read budget of this serial is exhausted (no request sent); "
                            "last failed read: HTTP 500 after 3 attempt(s)")], detail
    # the budget is unchanged: two invoked reads (3 attempts each) and nothing more for this serial
    assert len([p for _m, p, _d in ctrl.calls if BULK + SN2 in p]) == 6


def test_a_failed_read_followed_by_a_valid_one_leaves_no_stale_reason():
    class FirstSummaryFails(V.VpcController):
        def __init__(self):
            super(FirstSummaryFails, self).__init__()
            self.summary_reads = 0

        def __call__(self, mod, method, path, data=None):
            if SUMMARY + SN1 in path:
                self.summary_reads += 1
                if self.summary_reads <= 3:
                    self.calls.append((method, path, data))
                    return {"RETURN_CODE": 500, "MESSAGE": CANARY, "DATA": {}}
            return super(FirstSummaryFails, self).__call__(mod, method, path, data)

    ctrl = FirstSummaryFails().seed_baseline()
    V.create_previews(ctrl)
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.summary_reads > 3 and "could not be read authoritatively" not in json.dumps(result)


def test_truly_absent_member_stays_absence_not_unreadable():
    ctrl = V.baseline_ctrl()
    del ctrl.nodes[SN1][M1]
    got = refused(ctrl)
    assert any("not an existing physical interface" in l for l in got)
    assert not any("could not be read authoritatively" in l for l in got)


# ------------------------------------------------------------------ member join and a mixed Po / vPC invocation
def test_join_names_the_unreadable_peer_even_when_it_receives_no_new_member():
    ctrl = MU.vpc_seeded({SN1: [M1], SN2: [M2]}, spare={SN1: [MU.E9P]})
    ctrl.read_failures.add(SUMMARY + SN2)
    got = refused(ctrl, [V.vpc_item(peer1_members=[M1, MU.E9P])])
    assert cause(SN2, "the interface summary of", "HTTP 500 after 3 attempt(s)") in got
    assert not any(SN1 in l for l in got)


def test_join_names_the_joining_peer_cause_once():
    ctrl = MU.vpc_seeded({SN1: [M1], SN2: [M2]}, spare={SN1: [MU.E9P]})
    ctrl.read_failures.add(POLICIES + SN1)
    got = refused(ctrl, [V.vpc_item(peer1_members=[M1, MU.E9P])])
    causes = [l for l in got if "the switch policy list of" in l]
    assert causes == [cause(SN1, "the switch policy list of", "HTTP 500 after 1 attempt(s)")], causes
    assert "{0} on {1}: {2}".format(MU.E9P, SN1, UNREAD) in got


def test_mixed_po_and_vpc_invocation_keeps_every_refusal_and_names_the_vpc_cause():
    ctrl = V.baseline_ctrl()
    nv = trunk_host_nv("Ethernet1/5")
    nv["ADMIN_STATE"] = None  # ADMIN-UP-JOIN: "true" now joins; an unknown administrative state is still refused
    ctrl.nodes[SN1]["Ethernet1/5"] = {"policy": TRUNK, "nvPairs": nv}
    ctrl.read_failures.add(SUMMARY + SN2)
    po = {"name": "port-channel50", "type": "pc", "switch": [V.IP1], "deploy": True,
          "profile": {"mode": "pvlan", "pvlan_mode": "host", "members": ["Ethernet1/5"], "admin_state": False,
                      "pvlan_association": [{"primary_vlan": V.PRIMARY, "secondary_vlan": V.SECONDARY}]}}
    got = refused(ctrl, [po, V.vpc_item()])
    assert any(l.startswith("Ethernet1/5 on %s: the member's administrative state is unknown" % SN1) for l in got)
    assert generic(SN2, M2) <= folded(got)
    assert cause(SN2, "the interface summary of", "HTTP 500 after 3 attempt(s)") in got
    assert not any(l.startswith("%s on %s" % (V.VPC, SN1)) for l in got)


def test_total_detail_failure_on_the_first_serial_is_still_the_earlier_refusal():
    """Documented limit, unchanged: the vPC parent's own HAVE is read through the pair's FIRST serial before this preflight."""
    ctrl = V.baseline_ctrl()
    ctrl.read_failures.add(BULK + SN1)
    status, result = V.run_vpc(ctrl, [V.vpc_item()])
    assert status == "fail" and mutating(ctrl) == []
    assert result["msg"].startswith("Current state of interface %s on %s could not be read authoritatively" % (V.VPC, V.PAIR))


def test_reason_classification_accepts_exactly_what_the_readers_accept():
    """Classifying a failure must not tighten a reader: every answer the readers took as `RETURN_CODE == 200` with a DATA list
    (an equal float included) gets no reason; every other answer gets controlled text without the body or message."""
    reason = dcnm_interface.response_failure_reason
    assert reason({"RETURN_CODE": 200, "DATA": []}, 3) is None
    assert reason({"RETURN_CODE": 200.0, "DATA": []}, 3) is None
    assert reason({"RETURN_CODE": 200, "DATA": {"x": CANARY}}, 3) == "the response DATA is not a list"
    assert reason({"RETURN_CODE": 500, "MESSAGE": CANARY}, 3) == "HTTP 500 after 3 attempt(s)"
    assert reason({"RETURN_CODE": True, "DATA": []}, 1) == "the response has no integer status"
    assert reason({"RETURN_CODE": "200", "DATA": []}, 1) == "the response has no integer status"
    assert reason(None, 1) == "no response (transport error) after 1 attempt(s)"
    assert reason([], 1) == "the response body is empty"
    assert reason(CANARY, 1) == "the response is not an object"
