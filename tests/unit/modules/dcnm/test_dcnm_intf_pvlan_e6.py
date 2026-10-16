"""E6 (E5-R1-01): the summary's ifType/isPhysical can no longer hide a PVLAN policy known in the detail.

E5 excluded a port whose summary entry said `isPhysical: false` (with a trunk underlay) BEFORE looking at
the detail, so a `replaced` conversion of a port whose detail is int_pvlan_host was modified and deployed
with no PVLAN gate. SYNTHETIC type/policy contradictions on the MEASURED response shape.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from .test_dcnm_intf_pvlan_e4 import (
    ADD_2212,
    DEPLOY,
    IF7,
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

TYPE_CONFLICT = "the detail holds int_pvlan_host but the interface summary describes"


def writes(c):
    return c.requests("POST", MODIFY) + c.requests("POST", DEPLOY)


def nonphysical(c, template, **types):
    fields = {"isPhysical": "false"}
    fields.update(types)
    c.summary[IF7] = dict(fields, underlayPolicies=[under(c, templateName=template)])
    return c


# ===================================================================================== the probe case
class TestProbeReplacedCase:

    def test_replaced_conversion_with_contradictory_summary_type_sends_nothing(self):
        c = nonphysical(ctrl(), TRUNK)
        c.previews = [reset_preview()]
        status, res = run(c, [trunk_item(IF7)], state="replaced")
        assert status == "fail" and TYPE_CONFLICT in res["msg"] and "No configuration or deployment request was sent" in res["msg"], res
        assert writes(c) == [] and c.requests(mark=PREVIEW_MARK) == []

    def test_consistent_conversion_keeps_its_gate(self):
        c = ctrl()
        c.previews = [reset_preview()]
        status, res = run(c, [trunk_item(IF7)], state="replaced")
        assert c.requests(mark=PREVIEW_MARK), res  # reaches the pre-deploy gate (its verdict is E3's)
        assert len(c.requests("POST", DEPLOY)) == 0 or c.order().index("PREVIEW") < c.order().index("DEPLOY")

    def test_deleted_variant_stays_a_no_op(self):
        # Not generalized (mandate): the review probe returns no operation for deleted in this harness.
        c = nonphysical(ctrl(), TRUNK)
        status, res = run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")
        assert writes(c) == []


# ===================================================================================== every detail origin
class TestSameDecisionForEveryOrigin:

    @pytest.mark.parametrize("origin", ["have", "cache", "new-read"])
    @pytest.mark.parametrize("types", [{"isPhysical": "false"}, {"ifType": "INTERFACE_PORT_CHANNEL"}, {"ifType": "INTERFACE_VLAN", "isPhysical": "false"}])
    def test_pvlan_detail_against_a_non_physical_summary_is_unknown(self, origin, types):
        d = PreStateDouble(entry_for(IF7, TRUNK, **types), detail=(PVLAN, {"PVLAN_MODE": "host"}))
        detail = {"policy": PVLAN, "interfaces": [{"ifName": IF7, "serialNumber": SERIAL, "nvPairs": {"PVLAN_MODE": "host"}}]}
        if origin == "have":
            d.have = [copy.deepcopy(detail)]
        elif origin == "cache":
            d.intf_detail_cache[(SERIAL, IF7.lower())] = copy.deepcopy(detail)
        state, reason, nv = d.pre(IF7)
        assert state == "unknown" and reason.startswith(TYPE_CONFLICT) and nv is None


# ===================================================================================== both directions
class TestContradictionsInBothDirections:

    def test_pvlan_in_detail_non_physical_trunk_summary(self):
        d = PreStateDouble(entry_for(IF7, TRUNK, isPhysical="false"), detail=(PVLAN, {}))
        assert d.pre(IF7)[0] == "unknown"

    def test_pvlan_in_summary_non_physical_pvlan_detail(self):
        d = PreStateDouble(entry_for(IF7, PVLAN, isPhysical="false"), detail=(PVLAN, {}))
        assert d.pre(IF7)[0] == "unknown"

    def test_pvlan_in_summary_non_physical_trunk_detail(self):
        d = PreStateDouble(entry_for(IF7, PVLAN, isPhysical="false"), detail=(TRUNK, {}))
        state, reason, _nv = d.pre(IF7)
        assert state == "unknown" and "names int_pvlan_host" in reason

    def test_pvlan_in_summary_non_physical_absent_detail(self):
        d = PreStateDouble(entry_for(IF7, PVLAN, isPhysical="false"), detail="absent")
        assert d.pre(IF7)[0] == "unknown"

    def test_main_merged_trunk_with_a_non_physical_pvlan_summary_sends_nothing(self):
        c = FakeController()
        c.detail[IF7] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF7)}
        nonphysical(c, PVLAN)
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged")
        assert status == "fail" and writes(c) == []

    def test_main_pvlan_merge_with_a_non_physical_summary_sends_nothing(self):
        c = nonphysical(ctrl(), PVLAN)
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "not a standalone physical Ethernet" in res["msg"] and writes(c) == []


# ===================================================================================== kept behavior
class TestKept:

    def test_non_physical_without_any_pvlan_indication_is_still_excluded(self):
        d = PreStateDouble(entry_for(IF7, TRUNK, isPhysical="false"), detail=(TRUNK, {}))
        assert d.pre(IF7) == ("known", TRUNK, None) and d.reads == ["detail"]  # one bulk read per switch

    def test_non_physical_with_unreadable_policy_and_no_pvlan_detail_is_excluded(self):
        d = PreStateDouble(entry_for(IF7, isPhysical="false", underlayPolicies=[{"source": ""}]), detail="absent")
        assert d.pre(IF7) == ("known", None, None)

    @pytest.mark.parametrize(
        "name,sno", [("port-channel300", SERIAL), ("Loopback200", SERIAL), ("Ethernet1/3.2", SERIAL), ("vlan2001", SERIAL), ("vPC150", "FOX1821H035~" + SERIAL)]
    )
    def test_identity_exclusions_need_no_read(self, name, sno):
        d = PreStateDouble(entry_for(IF7, PVLAN), detail=(PVLAN, {}))
        assert module.DcnmIntf.dcnm_intf_pvlan_pre_state(d, name, sno) == ("known", None, None) and d.reads == []

    def test_authoritative_absence_is_still_a_creation(self):
        d = PreStateDouble(None)
        d.have_all_cached_snos = set()
        d.intf_detail_authoritative_absent_keys.add((SERIAL, IF7.lower()))
        assert d.pre(IF7) == ("absent", None, None) and d.reads == []

    def test_pvlan_reset_and_redeploy_keep_their_gates(self):
        c = ctrl()
        c.previews = [reset_preview()]
        assert run(c, [{"name": IF7, "switch": [SWITCH_IP]}], state="deleted")[0] == "exit" and c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]
        from .test_dcnm_intf_pvlan_e4 import pvlan_nv

        c = ctrl(pvlan_nv("G6-M0b"))
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")]
        assert run(c, [pvlan_item(**ADD_2212)])[0] == "exit" and c.order() == ["PREVIEW", "DEPLOY"]

    def test_member_port_is_still_refused(self):
        member = "int_port_channel_trunk_member_11_1"
        c = ctrl({"PO_ID": "Port-channel5", "INTF_NAME": IF7, "DESC": "", "ADMIN_STATE": "true", "CONF": ""}, member)
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "port-channel or vPC member" in res["msg"] and writes(c) == []

    def test_consistent_trunk_control_is_unchanged(self):
        c = FakeController()
        c.detail[IF7] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF7)}
        status, res = run(c, [trunk_item(IF7, allowed_vlans="10")], state="merged")
        assert status == "exit" and c.order() == ["MODIFY", "DEPLOY"]
