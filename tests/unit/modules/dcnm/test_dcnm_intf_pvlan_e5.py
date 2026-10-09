"""E5 (E4-R1-01): one current-policy resolution for self.have, the detail cache and a new read.

E4 returned a non-PVLAN detail found in self.have or in the detail cache BEFORE looking at the
interface summary, so a summary whose valid nested underlay names int_pvlan_host was never contrasted
and a merged change on that port was modified and deployed with no PVLAN gate. SYNTHETIC disagreement
built on the MEASURED response shape (no `policy` is added to any raw answer).
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from .test_dcnm_intf_pvlan_e4 import (
    ADD_2212,
    DEPLOY,
    IF7,
    IF8,
    MEASURED,
    MODIFY,
    PREVIEW_MARK,
    PVLAN,
    SERIAL,
    SWITCH_IP,
    TRUNK,
    FakeController,
    PreStateDouble,
    ctrl,
    entry_for,
    measured_preview,
    module,
    pvlan_item,
    reset_preview,
    run,
    trunk_host_nv,
    trunk_item,
    under,
)

CONFLICT = "the interface summary names int_pvlan_host but the detail holds 'int_trunk_host'"
SUMMARY_READ = "/rest/interface/detail?serialNumber="
DETAIL_BULK = "/rest/interface?serialNumber=%s" % SERIAL


def trunk_ctrl(names=(IF7,), pvlan_summary=()):
    c = FakeController()
    for name in names:
        c.detail[name] = {"policy": TRUNK, "nvPairs": trunk_host_nv(name)}
    for name in pvlan_summary:
        c.summary[name] = {"underlayPolicies": [under(c, name, templateName=PVLAN)]}
    return c


def writes(c):
    return c.requests("POST", MODIFY) + c.requests("POST", DEPLOY)


# ===================================================================================== 1. the probe case
class TestProbeCaseThroughMain:

    def test_conflicting_summary_refuses_before_any_write(self):
        c = trunk_ctrl(pvlan_summary=(IF7,))
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged")
        assert status == "fail" and CONFLICT in res["msg"] and "No configuration or deployment request was sent" in res["msg"], res
        assert writes(c) == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_consistent_trunk_control_is_unchanged(self):
        c = trunk_ctrl()
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged")
        assert status == "exit", res
        assert c.order() == ["MODIFY", "DEPLOY"] and c.requests(mark=PREVIEW_MARK) == []


# ===================================================================================== 2. symmetry
class TestSameDecisionForEveryDetailOrigin:

    def _double(self, origin):
        d = PreStateDouble(entry_for(IF7, PVLAN), detail=(TRUNK, {}))
        trunk = {"policy": TRUNK, "interfaces": [{"ifName": IF7, "serialNumber": SERIAL, "nvPairs": {}}]}
        if origin == "have":
            d.have = [copy.deepcopy(trunk)]
        elif origin == "cache":
            d.intf_detail_cache[(SERIAL, IF7.lower())] = copy.deepcopy(trunk)
        return d

    @pytest.mark.parametrize("origin", ["have", "cache", "new-read"])
    def test_pre_state_conflict(self, origin):
        d = self._double(origin)
        assert d.pre(IF7) == ("unknown", CONFLICT, None)
        assert d.reads == ([] if origin != "new-read" else ["detail"])  # summary already loaded: never re-read

    @pytest.mark.parametrize(
        "state,config,unlisted",
        [
            ("merged", [trunk_item(IF7, allowed_vlans="10")], False),  # detail through self.have
            ("deleted", [{"name": IF7, "switch": [SWITCH_IP]}], False),  # reset of the listed port
            ("overridden", [trunk_item(IF7, allowed_vlans="10")], True),  # unlisted IF8 reset: detail cache
        ],
        ids=["merged-have", "deleted", "overridden-unlisted"],
    )
    def test_main_refuses_the_same_way(self, state, config, unlisted):
        target = IF8 if unlisted else IF7
        c = trunk_ctrl(names=(IF7, IF8), pvlan_summary=(target,))
        for name in (IF7, IF8):  # non-default, so deleted/overridden have a reset to send
            c.detail[name]["nvPairs"]["DESC"] = "non-default"
        status, res = run(c, copy.deepcopy(config), state=state)
        assert status == "fail" and CONFLICT in res["msg"] and target + " on " + SERIAL in res["msg"], res
        assert writes(c) == []

    @pytest.mark.parametrize(
        "state,config",
        [
            ("merged", [trunk_item(IF7, allowed_vlans="10")]),
            ("deleted", [{"name": IF7, "switch": [SWITCH_IP]}]),
            ("overridden", [trunk_item(IF7, allowed_vlans="10")]),
        ],
        ids=["merged", "deleted", "overridden"],
    )
    def test_consistent_controls_keep_their_generic_behavior(self, state, config):
        c = trunk_ctrl(names=(IF7, IF8))
        for name in (IF7, IF8):
            c.detail[name]["nvPairs"]["DESC"] = "non-default"
        status, res = run(c, copy.deepcopy(config), state=state)
        assert status == "exit", res
        assert c.requests("POST", MODIFY) and c.requests(mark=PREVIEW_MARK) == []  # the generic write happens, ungated

    def test_reads_stay_per_switch(self):
        names = ("Ethernet1/7", "Ethernet1/8", "Ethernet1/9", "Ethernet1/10")
        c = trunk_ctrl(names=names)
        for n in names[1:]:
            c.detail[n]["nvPairs"]["DESC"] = "non-default"
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="overridden")
        assert status == "exit", res
        assert len(c.requests("GET", SUMMARY_READ)) <= 2  # the generic read plus at most one PVLAN read, not per interface
        assert len([r for r in c.requests("GET") if r[1].endswith(DETAIL_BULK)]) <= 2


# ===================================================================================== 3. authoritative absence
class TestAuthoritativeAbsenceAgainstTheSummary:

    def _absent(self, entry, summary_ok=True):
        d = PreStateDouble(entry, summary_ok=summary_ok)
        d.intf_detail_authoritative_absent_keys.add((SERIAL, IF7.lower()))
        return d

    def test_absent_detail_against_a_pvlan_summary_is_unknown(self):
        d = self._absent(entry_for(IF7, PVLAN))
        state, reason, _nv = d.pre(IF7)
        assert state == "unknown" and "names int_pvlan_host but the detail holds None" in reason and d.reads == []

    def test_absent_detail_against_an_unreadable_summary_entry_is_unknown(self):
        d = self._absent(entry_for(IF7, underlayPolicies="garbage"))
        assert d.pre(IF7)[0] == "unknown"

    def test_absent_detail_with_a_failed_summary_names_nothing(self):
        d = self._absent(None, summary_ok=False)
        assert d.pre(IF7) == ("absent", None, None) and d.reads == []

    def test_absent_detail_without_any_summary_read_is_a_creation(self):
        d = self._absent(None)
        d.have_all_cached_snos = set()  # this invocation never loaded the summary
        assert d.pre(IF7) == ("absent", None, None) and d.reads == []  # no new read on a creation

    def test_absent_detail_with_a_non_pvlan_summary_stays_non_pvlan(self):
        assert self._absent(entry_for(IF7, TRUNK)).pre(IF7) == ("known", TRUNK, None)


# ===================================================================================== 4. kept refusals and gates
class TestKeptBehavior:

    def test_summary_trunk_against_detail_pvlan_is_still_refused(self):
        c = ctrl()
        c.summary[IF7] = {"underlayPolicies": [under(c, templateName=TRUNK)]}
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "fail" and "disagrees" in res["msg"] and writes(c) == []

    @pytest.mark.parametrize(
        "name,sno", [("port-channel300", SERIAL), ("Loopback200", SERIAL), ("Ethernet1/3.2", SERIAL), ("vlan2001", SERIAL), ("vPC150", "FOX1821H035~" + SERIAL)]
    )
    def test_structural_exclusions_need_no_read(self, name, sno):
        d = PreStateDouble(entry_for(IF7, PVLAN), detail=(PVLAN, {}))
        assert module.DcnmIntf.dcnm_intf_pvlan_pre_state(d, name, sno) == ("known", None, None)
        assert d.reads == []

    def test_policy_less_svi_entry_is_not_a_target(self):
        d = PreStateDouble(copy.deepcopy(MEASURED["Vlan1"]))
        assert d.pre("Vlan1") == ("known", None, None) and d.reads == []

    def test_valid_pvlan_merge_still_passes_its_gate(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit" and c.order() == ["MODIFY", "PREVIEW", "DEPLOY"], res

    def test_pvlan_reset_still_goes_through_the_gate(self):
        c = ctrl()
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "exit" and c.order() == ["MODIFY", "PREVIEW", "DEPLOY"], res

    def test_conflict_in_check_mode_writes_nothing(self):
        c = trunk_ctrl(pvlan_summary=(IF7,))
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged", check_mode=True)
        assert status == "fail" and CONFLICT in res["msg"] and c.mutating() == []
