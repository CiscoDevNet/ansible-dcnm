"""E4: current-policy interpretation of the MEASURED interface summary for native Ethernet PVLAN.

MEASURED (NDFC 12.6.0.267): interface/detail carries no top-level `policy`; the policy identity is the
single nested `underlayPolicies` object. E3 read the top-level key, so on that shape it refused every
valid PVLAN merge and silently skipped the PVLAN gate for a `deleted` reset. These tests drive the real
main() (harness default = measured shape) and the real pre-state method against verbatim entries.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_e2 import OVERLAY_PROFILE
from .test_dcnm_intf_pvlan_e3 import NOT_OWNED, NOT_ROLLED_BACK, with_device_line
from .test_dcnm_intf_pvlan_harness import (
    DELETE,
    DEPLOY,
    IF7,
    IF8,
    MODIFY,
    PREVIEW_MARK,
    PVLAN,
    SERIAL,
    SWITCH_IP,
    TRUNK,
    FakeController,
    measured_preview,
    module,
    ok,
    pvlan_item,
    pvlan_nv,
    reset_preview,
    run,
    trunk_host_nv,
    trunk_item,
)

MEASURED = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "dcnm_intf_pvlan_summary_measured.json")))["entries"]
IF3 = "Ethernet1/3"
ADD_2212 = dict(pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])
NO_WRITE = "No configuration or deployment request was sent"
DEFECT_FRAGMENT = {
    "top_contradiction": "contradicts the underlay policy",
    "policy_id": "switch policy id",
    "entity": "targets Ethernet1/8",
    "serial": "on OTHER",
    "entity_type": "attached to a SWITCH",
    "null": "lists no underlay policy",
    "two": "lists 2 underlay policies",
    "missing_id": "lacks policyId",
    "source_overlay": "owned by another resource (source OVERLAY)",
}


def ctrl(nv=None, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv if nv is not None else pvlan_nv("G6-M0a", ifname=ifname))}
    return c


def deploys(c):
    return c.requests("POST", DEPLOY)


def each_deploy_follows_a_preview(c):
    kinds = ["P" if PREVIEW_MARK in p else "D" if p.endswith(DEPLOY) else "" for _m, p, _b in c.calls]
    kinds = [k for k in kinds if k]
    return all(i > 0 and kinds[i - 1] == "P" for i, k in enumerate(kinds) if k == "D")


def under(c, ifname=IF7, **changes):
    """The harness's measured-shape underlay object for `ifname`, with `changes` (DELETE removes a key)."""
    index = sorted(c.detail).index(ifname)
    u = {
        "source": "",
        "templateName": c.detail[ifname]["policy"],
        "policyId": c._policy_id(index),
        "entityName": ifname,
        "entityType": "INTERFACE",
        "serialNumber": SERIAL,
    }
    for key, value in changes.items():
        if value is DELETE:
            u.pop(key)
        else:
            u[key] = value
    return u


# ===================================================================================== helper units
class TestSummaryPolicyOnMeasuredEntries:

    def test_verbatim_entries(self):
        state, value = P.summary_policy(MEASURED[IF7], IF7)
        assert state == P.SUMMARY_KNOWN and value["templateName"] == TRUNK and value["policyId"] == "POLICY-174760" and value["source"] == ""
        state, value = P.summary_policy(MEASURED[IF3], IF3)
        assert state == P.SUMMARY_KNOWN and value["templateName"] == PVLAN and value["policyId"] == "POLICY-175820"
        assert P.summary_policy(MEASURED["Vlan1"], "Vlan1") == (P.SUMMARY_ABSENT, None)
        assert all("policy" not in e for e in MEASURED.values())  # the measured shape itself

    @pytest.mark.parametrize(
        "mutate,fragment",
        [
            (lambda e: e.pop("underlayPolicies"), "no underlay policy list (absent)"),
            (lambda e: e.__setitem__("underlayPolicies", e["underlayPolicies"][0]), "no underlay policy list (dict)"),
            (lambda e: e.__setitem__("underlayPolicies", e["underlayPolicies"] * 2), "lists 2 underlay policies"),
            (lambda e: e.__setitem__("underlayPolicies", [""]), "lists 1 underlay policies"),
            (lambda e: e["underlayPolicies"][0].pop("policyId"), "lacks policyId"),
            (lambda e: e["underlayPolicies"][0].__setitem__("policyId", ""), "lacks policyId"),
            (lambda e: e["underlayPolicies"][0].__setitem__("templateName", None), "lacks templateName"),
            (lambda e: e["underlayPolicies"][0].pop("source"), "no source string"),
            (lambda e: e["underlayPolicies"][0].__setitem__("entityName", IF8), "targets Ethernet1/8"),
            (lambda e: e["underlayPolicies"][0].__setitem__("serialNumber", "OTHER"), "targets Ethernet1/3 on OTHER"),
            (lambda e: e["underlayPolicies"][0].__setitem__("entityType", "SWITCH"), "attached to a SWITCH"),
            (lambda e: e.__setitem__("policy", TRUNK), "contradicts the underlay policy"),
        ],
    )
    def test_unknown_is_never_a_policy(self, mutate, fragment):
        entry = copy.deepcopy(MEASURED[IF3])
        mutate(entry)
        state, reason = P.summary_policy(entry, IF3)
        assert state == P.SUMMARY_UNKNOWN and fragment in reason, reason

    def test_consistent_top_level_policy_is_accepted(self):
        entry = dict(copy.deepcopy(MEASURED[IF3]), policy=PVLAN)
        assert P.summary_policy(entry, IF3)[0] == P.SUMMARY_KNOWN

    def test_top_level_policy_without_underlay_is_a_contradiction(self):
        entry = dict(copy.deepcopy(MEASURED["Vlan1"]), policy="int_vlan")
        assert P.summary_policy(entry, "Vlan1")[0] == P.SUMMARY_UNKNOWN

    def test_foreign_source_is_reported(self):
        entry = copy.deepcopy(MEASURED[IF3])
        entry["underlayPolicies"][0]["source"] = "OVERLAY"
        assert P.summary_policy(entry, IF3)[1]["source"] == "OVERLAY"
        entry["underlayPolicies"][0].pop("policyId")
        assert P.summary_policy(entry, IF3) == (P.SUMMARY_UNKNOWN, "its policy is owned by another resource (source OVERLAY)")

    def test_mentions_policy_reads_every_field(self):
        assert P.summary_mentions_policy(MEASURED[IF3], PVLAN) and not P.summary_mentions_policy(MEASURED[IF7], PVLAN)
        assert P.summary_mentions_policy({"underlayPolicies": {"templateName": PVLAN}}, PVLAN)
        assert P.summary_mentions_policy({"policy": PVLAN, "underlayPolicies": None}, PVLAN)
        assert not P.summary_mentions_policy(None, PVLAN)


# ===================================================================================== pre-state units (real method)
class PreStateDouble(object):
    """Only the state the real dcnm_intf_pvlan_pre_state reads; every read it makes is recorded."""

    _dcnm_intf_authority_key = module.DcnmIntf._dcnm_intf_authority_key
    PVLAN_PHYSICAL_ETHERNET_NAME = getattr(module.DcnmIntf, "PVLAN_PHYSICAL_ETHERNET_NAME", None)  # E4 only; lets E3 replay import

    def __init__(self, entry, detail="absent", summary_ok=True):
        self.have = []
        self.have_all = [entry] if entry is not None else []
        self.have_all_cached_snos = {SERIAL} if summary_ok else set()
        self.have_all_failed_snos = set() if summary_ok else {SERIAL}
        self.detail = detail  # "absent", "failed" or (policy, nvPairs)
        self.reads = []
        self.intf_detail_cache = {}  # nothing read yet in this invocation unless a test says so
        self.intf_detail_authoritative_absent_keys = set()
        self.intf_detail_cached_snos = set()

    def dcnm_intf_get_have_all_with_sno(self, sno):
        self.reads.append("summary")
        return False

    def dcnm_intf_bulk_fetch_intf_info(self, sno):
        self.reads.append("detail")

    def dcnm_intf_detail_unavailable(self, name, sno):
        return self.detail == "failed"

    def dcnm_intf_get_intf_info(self, name, sno, if_type):
        if self.detail == "absent":
            return []
        return {"policy": self.detail[0], "interfaces": [{"ifName": name, "serialNumber": sno, "nvPairs": copy.deepcopy(self.detail[1])}]}

    def pre(self, name):
        return module.DcnmIntf.dcnm_intf_pvlan_pre_state(self, name, SERIAL)


def entry_for(name, template=None, base=IF3, **changes):
    e = copy.deepcopy(MEASURED[base])
    e["ifName"] = name
    e["underlayPolicies"][0]["entityName"] = name
    if template:
        e["underlayPolicies"][0]["templateName"] = template
    e.update(changes)
    return e


class TestPreStateResolution:

    def test_known_pvlan_needs_the_detail_and_returns_its_nvpairs(self):
        d = PreStateDouble(entry_for(IF7), detail=(PVLAN, {"PVLAN_MODE": "host"}))
        assert d.pre(IF7) == ("known", PVLAN, {"PVLAN_MODE": "host"}) and d.reads == ["detail"]

    def test_known_non_pvlan_is_preserved_even_without_the_detail(self):
        for detail in ("absent", "failed", (TRUNK, {})):
            d = PreStateDouble(entry_for(IF7, TRUNK), detail=detail)
            assert d.pre(IF7) == ("known", TRUNK, None)

    def test_known_trunk_summary_with_pvlan_detail_is_a_pvlan_target(self):
        # The caller's ownership check then refuses the disagreement; it is never skipped.
        d = PreStateDouble(entry_for(IF7, TRUNK), detail=(PVLAN, {"PVLAN_MODE": "host"}))
        assert d.pre(IF7)[:2] == ("known", PVLAN)

    def test_policy_less_svi_is_not_a_target_without_any_read(self):
        d = PreStateDouble(copy.deepcopy(MEASURED["Vlan1"]))
        assert d.pre("Vlan1") == ("known", None, None) and d.reads == []

    @pytest.mark.parametrize(
        "name,sno", [("port-channel300", SERIAL), ("Loopback200", SERIAL), ("Ethernet1/3.2", SERIAL), ("vlan2001", SERIAL), ("vPC150", "FOX1821H035~" + SERIAL)]
    )
    def test_non_physical_ethernet_identities_are_never_targets(self, name, sno):
        d = PreStateDouble(None, summary_ok=False)
        assert module.DcnmIntf.dcnm_intf_pvlan_pre_state(d, name, sno) == ("known", None, None) and d.reads == []

    @pytest.mark.parametrize(
        "entry", [entry_for(IF7, ifType="INTERFACE_PORT_CHANNEL"), entry_for(IF7, isPhysical="false")], ids=["port-channel-type", "not-physical"]
    )
    def test_type_fields_exclude_pvlan_when_no_field_names_it(self, entry):
        entry["underlayPolicies"] = [{"source": ""}]  # unreadable identity, but never int_pvlan_host
        d = PreStateDouble(entry)
        # E6 (E5-R1-01): the type exclusion is judged after the detail is resolved (one bulk read per
        # switch), so that a known PVLAN detail can never be hidden; the E5 expectation was reads == [].
        assert d.pre(IF7) == ("known", None, None) and d.reads == ["detail"]

    def test_type_fields_do_not_hide_a_named_pvlan_policy(self):
        d = PreStateDouble(entry_for(IF7, isPhysical="false"), detail=(PVLAN, {"PVLAN_MODE": "host"}))
        # E6 (E5-R1-01): a PVLAN detail against a non-physical summary is a type/policy contradiction,
        # "unknown" (refused before any write). The E5 expectation was ("known", PVLAN), refused later by
        # the ownership check; both send nothing, E6 refuses it at registration for every detail origin.
        state, reason, _nv = d.pre(IF7)
        assert state == "unknown" and "not a physical Ethernet" in reason

    @pytest.mark.parametrize("detail,expected", [("absent", ("absent", None, None)), ((TRUNK, {}), ("known", TRUNK, None))])
    def test_physical_port_without_underlay_is_resolved_by_the_detail(self, detail, expected):
        d = PreStateDouble(entry_for(IF7, underlayPolicies=None), detail=detail)
        assert d.pre(IF7) == expected and d.reads == ["detail"]

    @pytest.mark.parametrize(
        "entry,detail",
        [
            (entry_for(IF7, underlayPolicies=[{"source": "", "templateName": PVLAN}]), (TRUNK, {})),  # names PVLAN, detail disagrees
            (entry_for(IF7, underlayPolicies=[{"source": "", "templateName": PVLAN}]), "failed"),
            (entry_for(IF7, underlayPolicies="garbage"), "failed"),
            (entry_for(IF7, underlayPolicies="garbage"), "absent"),
            (entry_for(IF7, underlayPolicies=None), "failed"),
            (entry_for(IF7, policy=PVLAN, underlayPolicies=None), (TRUNK, {})),
        ],
        ids=[
            "pvlan-named-detail-trunk",
            "pvlan-named-detail-failed",
            "garbage-detail-failed",
            "garbage-detail-absent",
            "absent-detail-failed",
            "top-pvlan-detail-trunk",
        ],
    )
    def test_unresolved_or_contradictory_state_is_unknown(self, entry, detail):
        d = PreStateDouble(entry, detail=detail)
        state, reason, nv = d.pre(IF7)
        assert state == "unknown" and isinstance(reason, str) and nv is None, (state, reason)

    def test_garbage_summary_with_a_positive_non_pvlan_detail_is_that_policy(self):
        d = PreStateDouble(entry_for(IF7, underlayPolicies="garbage"), detail=(TRUNK, {}))
        assert d.pre(IF7) == ("known", TRUNK, None)

    def test_detail_already_read_in_this_invocation_is_authoritative(self):
        d = PreStateDouble(None, summary_ok=False)
        d.intf_detail_cache[(SERIAL, IF7.lower())] = {"policy": PVLAN, "interfaces": [{"nvPairs": {"PVLAN_MODE": "host"}}]}
        assert d.pre(IF7) == ("known", PVLAN, {"PVLAN_MODE": "host"}) and d.reads == []
        d.intf_detail_cache[(SERIAL, IF7.lower())] = {"policy": TRUNK, "interfaces": [{"nvPairs": {}}]}
        assert d.pre(IF7) == ("known", TRUNK, None)

    def test_authoritative_detail_absence_is_a_creation_not_a_reset(self):
        d = PreStateDouble(None, summary_ok=False)
        d.intf_detail_authoritative_absent_keys.add((SERIAL, IF7.lower()))
        assert d.pre(IF7) == ("absent", None, None) and d.reads == []

    def test_unreadable_summary_is_unknown_and_not_absent(self):
        # E5 (E4-R1-01): the detail is now always resolved, and an already failed summary is not
        # re-read per interface. Both authorities unreadable stays "unknown" (the E4 verdict); an
        # authoritative detail absence with an unreadable summary is covered in test_dcnm_intf_pvlan_e5.
        d = PreStateDouble(None, summary_ok=False, detail="failed")
        assert d.pre(IF7)[0] == "unknown" and d.reads == []  # neither authority is re-read

    def test_interface_missing_from_an_authoritative_summary_is_absent(self):
        assert PreStateDouble(None).pre(IF7) == ("absent", None, None)

    def test_two_summary_entries_are_unknown(self):
        d = PreStateDouble(entry_for(IF7))
        d.have_all.append(entry_for(IF7))
        assert d.pre(IF7)[0] == "unknown"


# ===================================================================================== real main(), measured shape
class TestMergedOnTheMeasuredShape:

    def test_verbatim_summary_entry_valid_merge_passes_its_gate(self):
        c = ctrl(ifname=IF3)
        c.summary[IF3] = copy.deepcopy(MEASURED[IF3])  # verbatim (sanitized) measured entry
        c.policies_override = ok(
            [
                {
                    "entityName": IF3,
                    "entityType": "INTERFACE",
                    "templateName": PVLAN,
                    "source": "",
                    "deleted": False,
                    "policyId": "POLICY-175820",
                    "priority": 500,
                    "serialNumber": SERIAL,
                }
            ]
        )
        c.previews = [measured_preview("G6-M0b", ifname=IF3)]
        status, res = run(c, [pvlan_item(IF3, **ADD_2212)])
        assert status == "exit", res
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"] and each_deploy_follows_a_preview(c)

    def test_harness_default_is_the_measured_shape(self):
        c = ctrl()
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        summary = [r for r in c.calls if "/rest/interface/detail?serialNumber=" in r[1]]
        assert summary and "policy" not in c._summary_list()[0]

    def test_consistent_top_level_policy_control(self):
        c = ctrl()
        c.summary_top_policy = True
        c.previews = [measured_preview("G6-M0b")]
        assert run(c, [pvlan_item(**ADD_2212)])[0] == "exit"

    @pytest.mark.parametrize("deploy", [True, False])
    def test_check_mode_reaches_the_e3_check_mode_gate_not_ownership(self, deploy):
        c = ctrl()
        status, res = run(c, [pvlan_item(deploy=deploy, **ADD_2212)], check_mode=True)
        assert status == "fail" and "could not be verified in check mode" in res["msg"] and "summary policy" not in res["msg"], res
        assert c.mutating() == []

    @pytest.mark.parametrize("kind", sorted(DEFECT_FRAGMENT))
    @pytest.mark.parametrize("check_mode", [False, True])
    def test_ownership_defects_refuse_before_any_write(self, kind, check_mode):
        c = ctrl()
        c.summary[IF7] = {
            "top_contradiction": {"policy": TRUNK},
            "policy_id": {"underlayPolicies": [under(c, policyId="POLICY-999")]},
            "entity": {"underlayPolicies": [under(c, entityName=IF8)]},
            "serial": {"underlayPolicies": [under(c, serialNumber="OTHER")]},
            "entity_type": {"underlayPolicies": [under(c, entityType="SWITCH")]},
            "null": {"underlayPolicies": None},
            "two": {"underlayPolicies": [under(c), under(c)]},
            "missing_id": {"underlayPolicies": [under(c, policyId=DELETE)]},
            "source_overlay": {"underlayPolicies": [under(c, source="OVERLAY")]},
        }[kind]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_mode=check_mode)
        assert status == "fail" and NO_WRITE in res["msg"] and DEFECT_FRAGMENT[kind] in res["msg"], res
        assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_detail_policy_id_must_match_the_summary(self):
        nv = dict(pvlan_nv("G6-M0a"), POLICY_ID="POLICY-555")
        c = ctrl(nv)
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "POLICY_ID" in res["msg"] and c.mutating() == []

    def test_attachment_second_live_policy_is_refused(self):
        c = ctrl()
        c.policies_extra = [copy.deepcopy(OVERLAY_PROFILE)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "2 live policies" in res["msg"] and c.mutating() == []

    def test_port_channel_member_is_refused_on_the_measured_shape(self):
        member = "int_port_channel_trunk_member_11_1"
        c = ctrl({"PO_ID": "Port-channel5", "INTF_NAME": IF7, "DESC": "", "ADMIN_STATE": "true", "CONF": ""}, member)
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "port-channel or vPC member" in res["msg"] and c.mutating() == []


class TestResetAndOtherPreStatePaths:

    def test_deleted_reset_of_a_pvlan_port_is_registered_and_gated(self):
        c = ctrl()
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "exit", res
        assert c.sent_nv()[0] == TRUNK and c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]

    def test_invalid_reset_preview_sends_no_deploy_and_reports_the_pending_intent(self):
        c = ctrl()
        c.previews = [with_device_line(reset_preview(), "ip access-group KEEP-IN in")]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "fail" and NOT_OWNED in res["msg"] and NOT_ROLLED_BACK in res["msg"]
        assert deploys(c) == [] and len(c.requests("POST", MODIFY)) == 1

    @pytest.mark.parametrize("kind", ["overlay_policy", "policy_id", "missing_id", "top_contradiction"])
    def test_deleted_reset_ownership_error_sends_nothing(self, kind):
        c = ctrl()
        if kind == "overlay_policy":
            c.policies_extra = [copy.deepcopy(OVERLAY_PROFILE)]
        else:
            c.summary[IF7] = {
                "policy_id": {"underlayPolicies": [under(c, policyId="POLICY-999")]},
                "missing_id": {"underlayPolicies": [under(c, policyId=DELETE)]},
                "top_contradiction": {"policy": TRUNK},
            }[kind]
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "fail" and c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == [], res
        fragment = {"overlay_policy": "2 live policies", "policy_id": "switch policy id", "missing_id": "lacks policyId", "top_contradiction": "contradicts"}[
            kind
        ]
        assert fragment in res["msg"], res

    def test_deleted_reset_when_summary_says_trunk_but_detail_is_pvlan(self):
        c = ctrl()
        c.summary[IF7] = {"underlayPolicies": [under(c, templateName=TRUNK)]}
        c.previews = [reset_preview()]
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert status == "fail" and "disagrees" in res["msg"] and c.mutating() == []

    def test_overridden_resets_an_unlisted_pvlan_port_through_the_gate(self):
        c = ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.previews = [reset_preview(IF8)]
        keep = pvlan_item(
            pvlan_mode="trunk promiscuous",
            admin_state=False,
            native_vlan="2301",
            allowed_vlans="2301",
            pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
        )
        status, res = run(c, [keep], state="overridden")
        assert status == "exit", res
        assert c.sent_nv(IF8)[0] == TRUNK and c.sent_nv(IF7) is None and each_deploy_follows_a_preview(c)
        assert len(c.requests(mark=PREVIEW_MARK)) >= 1

    def test_overridden_with_an_unknown_unlisted_pvlan_port_sends_nothing(self):
        c = ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary[IF8] = {"underlayPolicies": [under(c, IF8, policyId=DELETE)]}
        keep = pvlan_item(
            pvlan_mode="trunk promiscuous",
            admin_state=False,
            native_vlan="2301",
            allowed_vlans="2301",
            pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
        )
        status, res = run(c, [keep], state="overridden")
        assert status == "fail" and c.mutating() == [], res

    def test_conversion_of_a_pvlan_port_to_trunk_reaches_the_gate(self):
        c = ctrl()
        c.previews = [reset_preview()]
        status, res = run(c, [trunk_item(IF7)], state="replaced")
        # E3 on this shape refused at ownership before any request; E4 lets the conversion reach the
        # PVLAN pre-deploy gate, whose verdict on this preview is the existing E3 behavior.
        assert c.requests(mark=PREVIEW_MARK) or status == "fail", res
        assert "summary policy None" not in res.get("msg", "")
        assert each_deploy_follows_a_preview(c)

    def test_out_of_sync_redeploy_goes_through_the_gate(self):
        c = ctrl(pvlan_nv("G6-M0b"))
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        assert c.order() == ["PREVIEW", "DEPLOY"]


class TestNonPvlanPreserved:

    def _calls(self, top):
        c = FakeController()
        c.detail[IF8] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF8)}
        c.summary_top_policy = top
        return c

    @pytest.mark.parametrize(
        "config,state",
        [([{"name": IF8, "switch": [SWITCH_IP]}], "deleted"), ([trunk_item(IF8, allowed_vlans="10")], "merged")],
        ids=["deleted-trunk", "merged-trunk"],
    )
    def test_trunk_port_requests_do_not_depend_on_the_summary_shape(self, config, state):
        measured, legacy = self._calls(False), self._calls(True)
        a, b = run(measured, copy.deepcopy(config), state=state), run(legacy, copy.deepcopy(config), state=state)
        assert a[0] == b[0] and measured.calls == legacy.calls
        assert measured.requests(mark=PREVIEW_MARK) == []
