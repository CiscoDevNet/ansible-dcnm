"""Native Ethernet PVLAN (int_pvlan_host): input, wire, state semantics, text commands and VLAN ranges."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import jinja2
import json
import pytest
import yaml

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .helpers.ethernet_controller import IF7
from .helpers.ethernet_controller import IF8
from .helpers.ethernet_controller import PREVIEW_MARK
from .helpers.ethernet_controller import PVLAN
from .helpers.ethernet_controller import TRANSITIONS
from .helpers.ethernet_controller import TRUNK
from .helpers.ethernet_controller import FakeController
from .helpers.ethernet_controller import measured_preview
from .helpers.ethernet_controller import pvlan_item
from .helpers.ethernet_controller import pvlan_nv
from .helpers.ethernet_controller import run
from .helpers.ethernet_controller import trunk_host_nv
from .helpers.ethernet_controller import trunk_item
from .helpers.ethernet_controller import HOST_A11
from .helpers.ethernet_controller import assert_no_writes
from .helpers.ethernet_controller import assoc
from .helpers.ethernet_controller import ctrl
from .helpers.ethernet_controller import DELETE
from .helpers.ethernet_controller import DEPLOY
from .helpers.ethernet_controller import FIXTURE
from .helpers.ethernet_controller import MODIFY
from .helpers.ethernet_controller import SERIAL
from .helpers.ethernet_controller import authority
from .helpers.ethernet_controller import ok
from .helpers.ethernet_controller import pending
from .helpers.ethernet_controller import preview
from .helpers.ethernet_controller import reset_preview
from .helpers.ethernet_controller import OVERLAY_PROFILE
from .helpers.ethernet_controller import DEVICE
from .helpers.ethernet_controller import SWITCH_IP
from .helpers import port_channel_controller as G5
from .helpers import vpc_modes as E1
from .helpers.vpc_controller import run_vpc


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan.py
# Native Ethernet PVLAN (int_pvlan_host): input, wire, state semantics and before-write gate.
#
# Every case drives the real main() through helpers/ethernet_controller (external boundary
# mocked only). Case IDs E01-E08 refer to the design's offline acceptance matrix.
# ====================================================================================================
TPROM_A11 = pvlan_nv("G6-M0a")
TPROM_BOTH = pvlan_nv("G6-M0b")
HOST_A12 = pvlan_nv("H3b")
PROM_A11 = pvlan_nv("PU1")
PROM_BOTH = pvlan_nv("PU2")
TSEC_A12 = pvlan_nv("TS1")


def mapping(*secondaries):
    return [{"primary_vlan": 2210, "secondary_vlans": ",".join(str(s) for s in secondaries)}]


def pairs(nv, key):
    """Sorted (P, S) pairs of a sent wrapper. Local on purpose: these real-main cases must import
    nothing new, so the same file exercises main() on the pinned base for fail-before evidence."""
    raw = nv.get(key, "")
    if raw == "":
        return []
    out = []
    for row in json.loads(raw)[key]:
        out.append((int(row["P_VLAN"]), int(row["S_VLAN"])))
    return sorted(out)


def diff_nv(result, bucket, ifname=IF7):
    for d in result["diff"][0][bucket]:
        for intf in d["interfaces"]:
            if intf["ifName"] == ifname:
                return intf["nvPairs"]
    return None


# ===================================================================================== E01
class TestE01FourModesWire:
    """Raw public types -> int_pvlan_host -> exact wrapper/scalar wire, one per mode."""

    def test_trunk_promiscuous_from_trunk_host(self):
        c = ctrl(trunk_host_nv(), TRUNK)
        c.previews = [measured_preview("G6-M0a")]
        status, res = run(
            c, [pvlan_item(pvlan_mode="trunk promiscuous", admin_state=False, pvlan_mapping=mapping(2211), native_vlan="2301", allowed_vlans="2301")]
        )
        assert status == "exit" and res["changed"] is True
        policy, nv = c.sent_nv()
        assert policy == PVLAN
        assert nv["PVLAN_MODE"] == "trunk promiscuous"
        assert nv["MAPPING_LIST"] == '{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"}]}'
        assert nv["ASSOCIATION_LIST"] == ""
        assert (nv["PVLAN_NATIVE_VLAN"], nv["PVLAN_ALLOWED_VLANS"]) == ("2301", "2301")
        assert nv["ADMIN_STATE"] == "false"
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]

    def test_host_from_trunk_host(self):
        c = ctrl(trunk_host_nv(), TRUNK)
        c.previews = [measured_preview("H3a")]
        status, res = run(c, [pvlan_item(pvlan_mode="host", admin_state=False, pvlan_association=assoc(2211))])
        assert status == "exit", res
        nv = c.sent_nv()[1]
        assert nv["ASSOCIATION_LIST"] == '{"ASSOCIATION_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"}]}'
        assert nv["MAPPING_LIST"] == "" and nv["PVLAN_NATIVE_VLAN"] == "" and nv["PVLAN_ALLOWED_VLANS"] == ""

    def test_promiscuous_from_host_replaced(self):
        c = ctrl(TRANSITIONS["PU1"]["pre_nv"])
        c.previews = [measured_preview("PU1")]
        status, res = run(c, [pvlan_item(pvlan_mode="promiscuous", admin_state=False, pvlan_mapping=mapping(2211))], state="replaced")
        assert status == "exit", res
        nv = c.sent_nv()[1]
        assert nv["PVLAN_MODE"] == "promiscuous"
        assert pairs(nv, "MAPPING_LIST") == [(2210, 2211)]
        assert nv["ASSOCIATION_LIST"] == '{"ASSOCIATION_LIST":[]}'  # inactive list cleared explicitly

    def test_trunk_secondary_isolated_replaced(self):
        c = ctrl(TRANSITIONS["TS1"]["pre_nv"])
        c.previews = [measured_preview("TS1")]
        status, res = run(
            c,
            [pvlan_item(pvlan_mode="trunk secondary", admin_state=False, pvlan_association=assoc(2212), native_vlan="2301", allowed_vlans="2301")],
            state="replaced",
        )
        assert status == "exit", res
        nv = c.sent_nv()[1]
        assert pairs(nv, "ASSOCIATION_LIST") == [(2210, 2212)]
        assert nv["MAPPING_LIST"] == '{"MAPPING_LIST":[]}'
        assert c.requests("GET", "/top-down/fabrics/test_fabric/networks")

    def test_unchanged_sibling_trunk_control_makes_no_pvlan_calls(self):
        c = ctrl(trunk_host_nv(IF8), TRUNK, IF8)
        status, res = run(c, [trunk_item(IF8, deploy=False, description="sibling")])
        assert status == "exit"
        assert c.requests(mark=PREVIEW_MARK) == []
        assert c.requests(mark="/top-down/") == [] and c.requests(mark="/configtemplate/") == []
        policy, nv = c.sent_nv(IF8)
        assert policy == TRUNK and "PVLAN_MODE" not in nv


# ===================================================================================== E02
BASE = dict(pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2211))
INVALID = [
    ({"pvlan_mode": None}, "pvlan_mode must not be null"),
    ({"pvlan_mode": "trunk"}, "pvlan_mode must be one of"),
    ({"pvlan_mapping": [{"primary_vlan": True, "secondary_vlans": "2211"}]}, "integer VLAN ID"),
    ({"pvlan_mapping": [{"primary_vlan": 0, "secondary_vlans": "2211"}]}, "outside 1-4094"),
    ({"pvlan_mapping": [{"primary_vlan": 4095, "secondary_vlans": "2211"}]}, "outside 1-4094"),
    ({"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2211,2211"}]}, "repeats VLAN"),
    ({"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212-2211"}]}, "not ascending"),
    (
        {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2211"}, {"primary_vlan": 2210, "secondary_vlans": "2211-2212"}]},
        "repeats a (primary, secondary) pair",
    ),
    ({"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2210"}]}, "with itself"),
    ({"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2211", "extra": 1}]}, "exactly the keys"),
    ({"pvlan_mapping": None}, "pvlan_mapping must not be null"),
    ({"pvlan_association": assoc(2211)}, "pvlan_association is not valid"),
    ({"native_vlan": 2301}, "native_vlan must be a string"),
    ({"native_vlan": "abc"}, "native_vlan must be"),
    ({"allowed_vlans": "all"}, "'all' is refused"),
    ({"allowed_vlans": "10-5"}, "not ascending"),
    ({"access_vlan": "10"}, "unsupported field"),
    ({"cmds": ["switchport private-vlan mapping 2210 2213"]}, "must not manage private-vlan"),
    ({"admin_state": "yes"}, "admin_state must be a boolean"),
    ({"pvlan_mode": "host", "pvlan_mapping": None, "pvlan_association": assoc(2211) + assoc(2212)}, None),
    (
        {"pvlan_mode": "promiscuous", "pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2211"}, {"primary_vlan": 2220, "secondary_vlans": "2221"}]},
        "single primary",
    ),
    ({"pvlan_mode": "trunk secondary", "pvlan_mapping": None, "pvlan_association": assoc(2211) + assoc(2212)}, "one secondary VLAN per primary"),
    ({"pvlan_mode": "host", "pvlan_mapping": None, "native_vlan": "2301"}, "valid only for pvlan_mode trunk"),
]


def invalid_profile(over):
    prof = dict(BASE)
    for k, v in over.items():
        if v is None and k == "pvlan_mapping" and "pvlan_association" in over:
            prof.pop(k, None)
        else:
            prof[k] = v
    return prof


class TestE02InvalidInputRefusedBeforeAnyWrite:

    @pytest.mark.parametrize("over,fragment", INVALID)
    @pytest.mark.parametrize("position", ["first", "second"])
    @pytest.mark.parametrize("check_mode", [False, True])
    def test_invalid_input(self, over, fragment, position, check_mode):
        c = ctrl(TPROM_A11)
        c.detail[IF8] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF8)}
        bad = pvlan_item(IF7, **invalid_profile(over))
        good = trunk_item(IF8, description="valid sibling")
        config = [bad, good] if position == "first" else [good, bad]
        status, res = run(c, config, check_mode=check_mode)
        assert status == "fail"
        if fragment:
            assert fragment in res["msg"]
        assert "No change was sent" in res["msg"]
        assert_no_writes(c)

    def test_host_two_associations_is_refused_with_limit_message(self):
        c = ctrl(HOST_A11)
        status, res = run(c, [pvlan_item(pvlan_mode="host", pvlan_association=assoc(2211) + assoc(2212))])
        assert status == "fail" and "at most one association" in res["msg"]
        assert_no_writes(c)


# ===================================================================================== E03
class TestE03MergedPreservesInActualRequest:

    def test_omitted_lists_scalars_and_companions_are_carried_in_full_request(self):
        c = ctrl(TPROM_BOTH)
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", description="web tier")])
        assert status == "exit" and res["changed"] is True
        nv = c.sent_nv()[1]
        assert nv["MAPPING_LIST"] == TPROM_BOTH["MAPPING_LIST"]  # HAVE bytes, not re-serialized
        assert (nv["PVLAN_NATIVE_VLAN"], nv["PVLAN_ALLOWED_VLANS"]) == ("2301", "2301")
        assert nv["ADMIN_STATE"] == "false"  # omitted companion preserved
        assert nv["lldpTransmit"] == "false" and nv["PTP"] == "false"  # unowned declared fields carried
        assert nv["DESC"] == "web tier"
        assert diff_nv(res, "merged") == {"DESC": "web tier"}  # diff == what changed
        for k in ("POLICY_ID", "PRIORITY", "SERIAL_NUMBER", "FABRIC_NAME", "POLICY_DESC", "MARK_DELETED"):
            assert k not in nv

    @pytest.mark.parametrize("value", [None, []])
    def test_omitted_or_empty_mapping_preserves_have(self, value):
        c = ctrl(TPROM_BOTH)
        prof = dict(pvlan_mode="trunk promiscuous", description="x")
        if value is not None:
            prof["pvlan_mapping"] = value
        status, res = run(c, [pvlan_item(deploy=False, **prof)])
        assert status == "exit"
        assert pairs(c.sent_nv()[1], "MAPPING_LIST") == [(2210, 2211), (2210, 2212)]

    def test_union_adds_and_deploys_through_the_gate(self):
        c = ctrl(TPROM_A11)
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2212))])
        assert status == "exit", res
        assert pairs(c.sent_nv()[1], "MAPPING_LIST") == [(2210, 2211), (2210, 2212)]
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]

    def test_conflicting_host_association_is_refused_after_union(self):
        c = ctrl(HOST_A11)
        status, res = run(c, [pvlan_item(pvlan_mode="host", pvlan_association=assoc(2212))])
        assert status == "fail" and "at most one association" in res["msg"]
        assert "No configuration or deployment request was sent" in res["msg"]
        assert_no_writes(c)

    def test_trunk_secondary_post_union_limit(self):
        c = ctrl(TSEC_A12)
        status, res = run(c, [pvlan_item(pvlan_mode="trunk secondary", pvlan_association=assoc(2211))])
        assert status == "fail" and "one secondary VLAN per primary" in res["msg"]
        assert_no_writes(c)


# ===================================================================================== E04
class TestE04ReplacedExactAndOmissionClears:

    def test_exact_list_and_cleared_trunk_scalars_agree_with_diff(self):
        c = ctrl(TPROM_BOTH)
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", admin_state=False, pvlan_mapping=mapping(2211))], state="replaced")
        assert status == "exit"
        nv = c.sent_nv()[1]
        assert pairs(nv, "MAPPING_LIST") == [(2210, 2211)]
        assert (nv["PVLAN_NATIVE_VLAN"], nv["PVLAN_ALLOWED_VLANS"]) == ("", "")
        reported = diff_nv(res, "replaced")
        assert set(reported) == {"MAPPING_LIST", "PVLAN_NATIVE_VLAN", "PVLAN_ALLOWED_VLANS"}
        assert all(reported[k] == nv[k] for k in reported)

    def test_allowed_none_is_distinct_from_unset(self):
        have = dict(TPROM_A11, PVLAN_ALLOWED_VLANS="")
        c = ctrl(have)
        status, res = run(
            c,
            [
                pvlan_item(
                    deploy=False, pvlan_mode="trunk promiscuous", admin_state=False, pvlan_mapping=mapping(2211), native_vlan="2301", allowed_vlans="none"
                )
            ],
            state="replaced",
        )
        assert status == "exit" and c.sent_nv()[1]["PVLAN_ALLOWED_VLANS"] == "none"
        assert diff_nv(res, "replaced") == {"PVLAN_ALLOWED_VLANS": "none"}

    def test_omission_alone_triggers_the_write(self):
        c = ctrl(TPROM_A11)
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", admin_state=False, pvlan_mapping=mapping(2211))], state="replaced")
        assert status == "exit" and res["changed"] is True
        assert diff_nv(res, "replaced") == {"PVLAN_NATIVE_VLAN": "", "PVLAN_ALLOWED_VLANS": ""}

    def test_replaced_omitted_list_is_cleared_with_the_empty_wrapper(self):
        c = ctrl(TPROM_A11)
        status, res = run(
            c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", admin_state=False, native_vlan="2301", allowed_vlans="2301")], state="replaced"
        )
        assert status == "exit"
        assert c.sent_nv()[1]["MAPPING_LIST"] == '{"MAPPING_LIST":[]}'


# ===================================================================================== E05
class TestE05EquivalenceAndIdempotency:

    @pytest.mark.parametrize("state", ["merged", "replaced"])
    @pytest.mark.parametrize("spelling", ["2211-2212", "2211,2212"])
    def test_in_sync_rerun_sends_nothing(self, state, spelling):
        c = ctrl(TPROM_BOTH)
        status, res = run(
            c,
            [
                pvlan_item(
                    pvlan_mode="trunk promiscuous",
                    admin_state=False,
                    pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": spelling}],
                    native_vlan="2301",
                    allowed_vlans="2301",
                )
            ],
            state=state,
        )
        assert status == "exit" and res["changed"] is False
        assert_no_writes(c)

    def test_reordered_have_rows_are_equal_and_have_bytes_survive_a_forced_write(self):
        have = dict(TPROM_BOTH, MAPPING_LIST='{"MAPPING_LIST":[{"P_VLAN":2210,"S_VLAN":"2212"},{"P_VLAN":"2210","S_VLAN":2211}]}')
        c = ctrl(have)
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2211, 2212), description="forced")])
        assert status == "exit"
        nv = c.sent_nv()[1]
        assert nv["MAPPING_LIST"] == have["MAPPING_LIST"]
        assert "MAPPING_LIST" not in diff_nv(res, "merged")


# ===================================================================================== E06
class TestE06NonTrunkPartialRemovalBlocked:

    @pytest.mark.parametrize("check_mode,deploy", [(False, True), (False, False), (True, True)])
    def test_strict_partial_removal_zero_writes(self, check_mode, deploy):
        c = ctrl(PROM_BOTH)
        status, res = run(
            c, [pvlan_item(deploy=deploy, pvlan_mode="promiscuous", admin_state=False, pvlan_mapping=mapping(2212))], state="replaced", check_mode=check_mode
        )
        assert status == "fail" and "promiscuous mapping that keeps other secondaries is blocked" in res["msg"]
        assert_no_writes(c)

    def test_mixed_remove_and_add_is_blocked(self):
        c = ctrl(PROM_BOTH)
        status, res = run(c, [pvlan_item(pvlan_mode="promiscuous", pvlan_mapping=mapping(2211, 2213))], state="replaced")
        assert status == "fail" and "2210/2212" in res["msg"]
        assert_no_writes(c)

    def test_blocked_second_object_stops_the_valid_first(self):
        c = ctrl(PROM_BOTH)
        c.detail[IF8] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF8)}
        status, res = run(
            c, [trunk_item(IF8, description="first is valid"), pvlan_item(pvlan_mode="promiscuous", pvlan_mapping=mapping(2211))], state="replaced"
        )
        assert status == "fail"
        assert_no_writes(c)

    def test_control_pure_addition_passes(self):
        c = ctrl(PROM_A11)
        c.previews = [measured_preview("PU2")]
        status, res = run(c, [pvlan_item(pvlan_mode="promiscuous", pvlan_mapping=mapping(2212))])
        assert status == "exit", res

    def test_control_full_clear_passes(self):
        c = ctrl(PROM_BOTH)
        c.previews = [measured_preview("PC1")]
        status, res = run(c, [pvlan_item(pvlan_mode="promiscuous", admin_state=False, pvlan_mapping=[])], state="replaced")
        assert status == "exit", res
        assert c.sent_nv()[1]["MAPPING_LIST"] == '{"MAPPING_LIST":[]}'

    def test_control_trunk_promiscuous_partial_removal_passes(self):
        c = ctrl(TPROM_BOTH)
        c.previews = [measured_preview("G6-M1")]
        status, res = run(
            c,
            [pvlan_item(pvlan_mode="trunk promiscuous", admin_state=False, pvlan_mapping=mapping(2211), native_vlan="2301", allowed_vlans="2301")],
            state="replaced",
        )
        assert status == "exit", res
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]


# ===================================================================================== E07
class TestE07SubmodeAndPolicyTransitions:

    def test_merged_submode_change_is_refused(self):
        c = ctrl(HOST_A11)
        status, res = run(c, [pvlan_item(pvlan_mode="promiscuous", pvlan_mapping=mapping(2211))])
        assert status == "fail" and "requires state replaced or overridden" in res["msg"]
        assert_no_writes(c)

    def test_replaced_submode_change_clears_stale_fields(self):
        c = ctrl(TRANSITIONS["TS1"]["pre_nv"])  # trunk promiscuous with native/allowed
        c.previews = [measured_preview("TS1")]
        status, res = run(
            c,
            [pvlan_item(pvlan_mode="trunk secondary", admin_state=False, pvlan_association=assoc(2212), native_vlan="2301", allowed_vlans="2301")],
            state="replaced",
        )
        assert status == "exit"
        nv = c.sent_nv()[1]
        assert nv["MAPPING_LIST"] == '{"MAPPING_LIST":[]}' and pairs(nv, "ASSOCIATION_LIST") == [(2210, 2212)]

    def test_leaving_trunk_mode_clears_native_and_allowed(self):
        c = ctrl(TPROM_A11)
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="host", admin_state=False, pvlan_association=assoc(2211))], state="replaced")
        assert status == "exit"
        nv = c.sent_nv()[1]
        assert (nv["PVLAN_NATIVE_VLAN"], nv["PVLAN_ALLOWED_VLANS"]) == ("", "")
        assert nv["MAPPING_LIST"] == '{"MAPPING_LIST":[]}'

    def test_entering_pvlan_carries_no_trunk_policy_data(self):
        c = ctrl(trunk_host_nv(), TRUNK)
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="host", pvlan_association=assoc(2211))])
        assert status == "exit"
        nv = c.sent_nv()[1]
        for k in ("ALLOWED_VLANS", "NATIVE_VLAN", "FEC", "GUARD_MODE", "aclFilter", "STORM_CONTROL_ACTION", "ENABLE_MONITOR"):
            assert k not in nv
        assert nv["ADMIN_STATE"] == "true"  # PVLAN parent default, not the old policy's value

    def test_exit_to_trunk_writes_the_trunk_parent(self):
        c = ctrl(TPROM_A11)
        status, res = run(c, [trunk_item(IF7, deploy=False, admin_state=False)], state="replaced")
        assert status == "exit"
        policy, nv = c.sent_nv()
        assert policy == TRUNK and "PVLAN_MODE" not in nv


# ===================================================================================== E08
class TestE08UnsafeCurrentStateRefused:

    def run_blocked(self, c, item=None, state="merged", fragment=None):
        status, res = run(c, [item or pvlan_item(pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2212))], state=state)
        assert status == "fail", res
        if fragment:
            assert fragment in res["msg"], res["msg"]
        assert_no_writes(c)
        return res

    def test_malformed_have_list(self):
        self.run_blocked(ctrl(dict(TPROM_A11, MAPPING_LIST='{"MAPPING_LIST":[{"P_VLAN":"x"}]}')), fragment="malformed")

    def test_null_have_list(self):
        self.run_blocked(ctrl(dict(TPROM_A11, MAPPING_LIST=None)), fragment="not a wrapper string")

    def test_unknown_have_mode(self):
        self.run_blocked(ctrl(dict(TPROM_A11, PVLAN_MODE="isolated")), fragment="not a known int_pvlan_host mode")

    def test_unclassified_have_field(self):
        self.run_blocked(ctrl(dict(TPROM_A11, newWritableField="on")), fragment="cannot classify")

    def test_detail_read_failure(self):
        c = ctrl(TPROM_A11)
        c.read_failures.add("/rest/interface?serialNumber=")
        status, res = run(c, [pvlan_item(pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2212))])
        assert status == "fail" and "could not be read authoritatively" in res["msg"]
        assert_no_writes(c)

    def test_summary_read_failure(self):
        c = ctrl(TPROM_A11)
        c.read_failures.add("/rest/interface/detail")
        self.run_blocked(c, fragment="summary could not be read authoritatively")

    def test_attachment_owned_port(self):
        c = ctrl(TPROM_A11)
        c.summary[IF7] = {"underlayPolicies": [{"source": "OVERLAY", "templateName": PVLAN}]}
        self.run_blocked(c, fragment="owned by another resource (source OVERLAY)")

    def test_port_channel_member_is_refused_before_member_rewrite(self):
        member = "int_port_channel_trunk_member_11_1"
        c = ctrl({"PO_ID": "Port-channel5", "INTF_NAME": IF7, "DESC": "", "ADMIN_STATE": "true", "CONF": ""}, member)
        self.run_blocked(c, fragment="port-channel or vPC member")

    def test_absent_physical_port_is_never_created(self):
        c = FakeController()
        c.detail[IF8] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF8)}
        self.run_blocked(c, fragment="never created through globalInterface")
        assert c.requests("POST", "/rest/globalInterface") == []

    def test_known_community_secondary_for_trunk_secondary(self):
        c = ctrl(TRANSITIONS["TS1"]["pre_nv"])
        self.run_blocked(c, pvlan_item(pvlan_mode="trunk secondary", pvlan_association=assoc(2211)), state="replaced", fragment="community VLAN")

    def test_unknown_secondary_type(self):
        c = ctrl(TRANSITIONS["TS1"]["pre_nv"])
        self.run_blocked(c, pvlan_item(pvlan_mode="trunk secondary", pvlan_association=assoc(2299)), state="replaced", fragment="cannot be established")

    def test_conflicting_secondary_type_metadata(self):
        c = ctrl(TRANSITIONS["TS1"]["pre_nv"])
        for n in c.networks:
            if '"2212"' in n["networkTemplateConfig"]:
                n["type"] = "Community"
                n["networkTemplateConfig"] = n["networkTemplateConfig"].replace('"Isolated"', '"Isolated"')
        self.run_blocked(c, pvlan_item(pvlan_mode="trunk secondary", pvlan_association=assoc(2212)), state="replaced", fragment="missing or conflicting")

    def test_network_read_failure(self):
        c = ctrl(TRANSITIONS["TS1"]["pre_nv"])
        c.read_failures.add("/top-down/fabrics/test_fabric/networks")
        self.run_blocked(
            c, pvlan_item(pvlan_mode="trunk secondary", pvlan_association=assoc(2212)), state="replaced", fragment="fabric networks could not be read"
        )

    def test_template_missing_declaration(self):
        c = ctrl(TPROM_A11)
        c.template = {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"content": "##template variables\nenum PVLAN_MODE;\n##template content\n"}}
        self.run_blocked(c, fragment="does not declare")

    def test_template_unreadable(self):
        c = ctrl(TPROM_A11)
        c.read_failures.add("/configtemplate/")
        self.run_blocked(c, fragment="template could not be read")

    def test_dcnm_11_is_refused_explicitly(self):
        c = ctrl(TPROM_A11)
        status, res = run(c, [pvlan_item(pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2212))], version=(11, None))
        assert status == "fail" and "requires NDFC 12" in res["msg"]
        assert_no_writes(c)

    def test_no_bulk_api_refuses_before_any_write(self):
        c = ctrl(TPROM_A11)
        status, res = run(c, [pvlan_item(pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2212))], bulk=False)
        assert status == "fail" and "bulk interface update API" in res["msg"]
        assert_no_writes(c)


# ===================================================================================== N06
N06 = "is associated with more than one primary VLAN"


def wire(key, *pairs_):
    return json.dumps({key: [{"P_VLAN": str(p), "S_VLAN": str(s)} for p, s in pairs_]}, separators=(",", ":"))


class TestN06OneSecondaryOnePrimary(object):
    """N06: a secondary VLAN may sit under ONE primary within an interface's resulting list. The check runs on the raw request and
    again on the final merged intent; only modifying/deploy calls are asserted absent (merged reads its current state first)."""

    def assert_n06(self, res, secondary=2212, primaries=(2210, 2410)):
        assert N06 in res["msg"], res["msg"]
        assert "secondary VLAN %d" % secondary in res["msg"]
        assert "(%s)" % ", ".join(str(p) for p in primaries) in res["msg"]

    @pytest.mark.parametrize("state", ["merged", "replaced"])
    def test_raw_trunk_promiscuous_request_alone_is_refused(self, state):
        c = ctrl(TPROM_A11)
        bad = [{"primary_vlan": 2210, "secondary_vlans": "2212"}, {"primary_vlan": 2410, "secondary_vlans": "2212"}]
        status, res = run(c, [pvlan_item(pvlan_mode="trunk promiscuous", pvlan_mapping=bad)], state=state)
        assert status == "fail"
        self.assert_n06(res)
        assert_no_writes(c)

    def test_raw_trunk_secondary_request_alone_is_refused(self):
        c = ctrl(TSEC_A12)
        status, res = run(c, [pvlan_item(pvlan_mode="trunk secondary", pvlan_association=assoc(2212) + assoc(2212, primary=2410))], state="replaced")
        assert status == "fail"
        self.assert_n06(res)
        assert_no_writes(c)

    def test_merged_union_with_the_current_mapping_is_refused(self):
        c = ctrl(TPROM_BOTH)  # current 2210/2211 + 2210/2212
        status, res = run(c, [pvlan_item(pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": 2410, "secondary_vlans": "2212"}])])
        assert status == "fail"
        self.assert_n06(res)
        assert "No configuration or deployment request was sent" in res["msg"]
        assert_no_writes(c)

    def test_merged_union_with_the_current_association_is_refused(self):
        c = ctrl(TSEC_A12)  # current 2210/2212; the trunk secondary one-secondary-per-primary limit does not catch this one
        status, res = run(c, [pvlan_item(pvlan_mode="trunk secondary", pvlan_association=assoc(2212, primary=2410))])
        assert status == "fail"
        self.assert_n06(res)
        assert "one secondary VLAN per primary" not in res["msg"]
        assert_no_writes(c)

    def test_replaced_validates_its_resulting_list_not_a_union(self):
        c = ctrl(TPROM_BOTH)
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": 2410, "secondary_vlans": "2212"}])],
                          state="replaced")
        assert status == "exit", res
        assert pairs(c.sent_nv()[1], "MAPPING_LIST") == [(2410, 2212)]

    def test_distinct_primaries_with_distinct_secondaries_stay_supported(self):
        c = ctrl(TPROM_A11)
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": 2410, "secondary_vlans": "2412"}])])
        assert status == "exit", res
        assert pairs(c.sent_nv()[1], "MAPPING_LIST") == [(2210, 2211), (2410, 2412)]

    def test_restating_a_current_pair_is_idempotent(self):
        c = ctrl(TPROM_BOTH)
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2212))])
        assert status == "exit" and res["changed"] is False, res
        assert c.mutating() == []

    def test_a_pair_repeated_in_one_request_keeps_its_own_refusal(self):
        c = ctrl(TPROM_A11)
        status, res = run(c, [pvlan_item(pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2212) + mapping(2212))])
        assert status == "fail" and "repeats a (primary, secondary) pair" in res["msg"] and N06 not in res["msg"]
        assert_no_writes(c)

    # ---- a current list that already holds the conflict (only possible from outside the module)
    def conflicted(self):
        nv = copy.deepcopy(TPROM_BOTH)
        nv["MAPPING_LIST"] = wire("MAPPING_LIST", (2210, 2212), (2410, 2212))
        return ctrl(nv)

    def test_merged_update_of_another_field_is_refused_on_its_resulting_list(self):
        c = self.conflicted()
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", description="x")])
        assert status == "fail"
        self.assert_n06(res)
        assert_no_writes(c)

    def test_replaced_with_a_valid_list_corrects_it(self):
        c = self.conflicted()
        status, res = run(c, [pvlan_item(deploy=False, pvlan_mode="trunk promiscuous", pvlan_mapping=mapping(2212))], state="replaced")
        assert status == "exit", res
        assert pairs(c.sent_nv()[1], "MAPPING_LIST") == [(2210, 2212)]

    @pytest.mark.parametrize("state", ["deleted", "query"])
    def test_deleted_and_query_gain_no_association_blocker(self, state):
        c = self.conflicted()
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state=state)
        assert N06 not in res.get("msg", ""), res.get("msg")
        if state == "query":
            assert status == "exit" and c.mutating() == [], res.get("msg")
        else:
            # the reset write is reached (no new pre-write blocker); its own deploy gate then asks for a preview this case does not give
            assert c.order()[:1] == ["MODIFY"], c.order()


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_e2.py
# Native Ethernet PVLAN: corrected behavior for the first review's findings.
#
# Every case drives the real main() through helpers/ethernet_controller; only external I/O is mocked. Response labels:
# MEASURED (discovery capture), DOCUMENTED (module source), SYNTHETIC (robustness counterexample, not a claim the controller
# emits it), TEMPLATE-PREDICTED (rendered from the pinned installed template, not measured).
# ====================================================================================================
ETH_REVIEW_TPROM_A11 = pvlan_nv("G6-M0a")
ETH_REVIEW_TPROM_BOTH = pvlan_nv("G6-M0b")
ADD_2212 = dict(pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])
KEEP_2211 = [
    pvlan_item(
        pvlan_mode="trunk promiscuous",
        admin_state=False,
        pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2211"}],
        native_vlan="2301",
        allowed_vlans="2301",
    )
]
TSEC_2212 = [
    pvlan_item(
        pvlan_mode="trunk secondary",
        admin_state=False,
        pvlan_association=[{"primary_vlan": 2210, "secondary_vlan": 2212}],
        native_vlan="2301",
        allowed_vlans="2301",
    )
]
MEASURED_SUCCESS = ok(copy.deepcopy(FIXTURE["deploy_success"]))  # MEASURED (names Ethernet1/7)


def eth_review_ctrl(nv=ETH_REVIEW_TPROM_A11, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv)}
    return c


def deploys(c):
    return c.requests("POST", DEPLOY)


def eth_review_assert_no_writes(c):
    assert c.mutating() == [], c.mutating()
    assert c.requests(mark=PREVIEW_MARK) == []


# ===================================================================================== F1
FAILED_BODIES = {
    "measured_500": {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": FIXTURE["deploy_500"]["data"]},  # MEASURED (PU3)
    "http500_dict": {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {"error": "synthetic"}},  # SYNTHETIC (R1-02/03)
    "dict_error": ok({"reportItemType": "ERROR", "message": "synthetic failure"}),  # SYNTHETIC
    "list_error": ok([{"reportItemType": "ERROR", "message": "CLI command failed", "entity": SERIAL + "~" + IF7}]),  # SYNTHETIC
    "empty_dict": ok({}),  # SYNTHETIC
    "unknown_key": ok({"message": "Interface deployed successfully", "value": [{"serialNumber": SERIAL, "IfName": IF7}], "x": 1}),
    "not_named": ok({"message": "Interface deployed successfully", "value": []}),  # SYNTHETIC
    "mixed_list": ok([{"reportItemType": "WARNING", "message": "No Commands to execute"}, {"reportItemType": "ERROR", "message": "x"}]),
}


class TestF1EveryDeployAttemptIsJudged:
    """A failed or indeterminate attempt fails the run even when every later read says In-Sync."""

    @pytest.mark.parametrize("kind", sorted(FAILED_BODIES))
    def test_primary_attempt(self, kind):
        c = eth_review_ctrl()
        c.previews = [measured_preview("G6-M0b"), measured_preview("G6-M0b", "post")]
        c.deploy_responses = [copy.deepcopy(FAILED_BODIES[kind])]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "attempt (deploy) failed or is indeterminate" in res["msg"]
        assert len(deploys(c)) == 1
        assert FAILED_BODIES[kind] in res["response"]  # the ORIGINAL response is retained
        assert res["pvlan_attempts"][-1]["site"] == "deploy"

    @pytest.mark.parametrize("kind", sorted(FAILED_BODIES))
    def test_check_deploy_resend_attempt_r1_02(self, kind):
        c = eth_review_ctrl()
        c.previews = [measured_preview("G6-M0b"), measured_preview("G6-M0b"), measured_preview("G6-M0b", "post")]
        c.deploy_responses = [copy.deepcopy(MEASURED_SUCCESS), copy.deepcopy(FAILED_BODIES[kind])]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "fail" and "attempt (check_deploy_resend) failed" in res["msg"]
        assert len(deploys(c)) == 2  # nothing after the failed resend
        assert "deploy Ethernet1/7@" + SERIAL + ": accepted" in res["msg"]  # partial progress is reported
        assert FAILED_BODIES[kind] in res["response"]

    @pytest.mark.parametrize("kind", sorted(FAILED_BODIES))
    def test_deployment_status_retry_attempt_r1_03(self, kind):
        c = eth_review_ctrl()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")] * 3 + [measured_preview("G6-M0b", "post")]
        c.compliance = ["Out-of-Sync"] * 9 + ["In-Sync"] * 20
        c.deploy_responses = [copy.deepcopy(MEASURED_SUCCESS)] * 2 + [copy.deepcopy(FAILED_BODIES[kind])]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "fail" and "attempt (deployment_status_retry) failed" in res["msg"]
        assert len(deploys(c)) == 3
        assert FAILED_BODIES[kind] in res["response"]

    def test_measured_success_at_every_attempt_passes(self):
        c = eth_review_ctrl()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")] * 3 + [measured_preview("G6-M0b", "post")] * 3
        c.compliance = ["Out-of-Sync"] * 9 + ["In-Sync"] * 20
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "exit", res
        assert [a["outcome"] for a in res.get("pvlan_attempts", [])] in ([], ["accepted"] * 3)

    def test_documented_benign_notice_with_matching_readback_passes(self):
        c = eth_review_ctrl()
        c.previews = [measured_preview("G6-M0b")]
        c.deploy_responses = [ok([{"reportItemType": "WARNING", "message": "No Commands to execute. In-Sync"}])]  # DOCUMENTED
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res


# ===================================================================================== F2
SUMMARY_DEFECTS = {
    "null": {"underlayPolicies": None},  # R1-07-null
    "absent": {"underlayPolicies": DELETE},
    "missing_source": {"underlayPolicies": [{"templateName": PVLAN}]},  # R1-07-missing-source
    "dict_container": {"underlayPolicies": {"source": ""}},
    "non_dict_entry": {"underlayPolicies": [""]},
    "multiple_direct": {"underlayPolicies": [{"source": "", "templateName": PVLAN}, {"source": "", "templateName": "second-policy"}]},
    "overlay_source": {"underlayPolicies": [{"source": "OVERLAY", "templateName": PVLAN}]},
    "template_mismatch": {"underlayPolicies": [{"source": "", "templateName": "int_access_host"}]},
    "summary_policy_mismatch": {"policy": "int_access_host"},
}
POLICY_DEFECTS = {
    "overlay_profile": ("extra", [OVERLAY_PROFILE]),
    "second_direct": ("extra", [{"entityName": IF7, "entityType": "INTERFACE", "templateName": TRUNK, "source": "", "deleted": False}]),
    "template_mismatch": ("override", ok([{"entityName": IF7, "entityType": "INTERFACE", "templateName": "int_access_host", "source": "", "deleted": False}])),
    "source_non_empty": ("override", ok([{"entityName": IF7, "entityType": "INTERFACE", "templateName": PVLAN, "source": "OVERLAY", "deleted": False}])),
    "malformed_entry": ("override", ok([{"entityName": IF7}])),
    "not_a_list": ("override", ok({"entityName": IF7})),
    "read_failure": ("override", {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}),
}


def apply_policy_defect(c, kind):
    how, value = POLICY_DEFECTS[kind]
    if how == "extra":
        c.policies_extra = copy.deepcopy(value)
    else:
        c.policies_override = copy.deepcopy(value)


class TestF2OwnershipAuthority:

    @pytest.mark.parametrize("kind", sorted(SUMMARY_DEFECTS))
    @pytest.mark.parametrize("check_mode,deploy", [(False, True), (False, False), (True, True)])
    def test_incomplete_or_conflicting_summary_refuses_before_any_write(self, kind, check_mode, deploy):
        c = eth_review_ctrl()
        c.summary[IF7] = copy.deepcopy(SUMMARY_DEFECTS[kind])
        status, res = run(c, [pvlan_item(deploy=deploy, **ADD_2212)], check_mode=check_mode)
        assert status == "fail" and "No configuration or deployment request was sent" in res["msg"], res
        eth_review_assert_no_writes(c)

    @pytest.mark.parametrize("kind", sorted(POLICY_DEFECTS))
    @pytest.mark.parametrize("check_mode", [False, True])
    def test_policy_list_must_show_one_direct_policy(self, kind, check_mode):
        c = eth_review_ctrl()
        apply_policy_defect(c, kind)
        status, res = run(c, [pvlan_item(**ADD_2212)], check_mode=check_mode)
        assert status == "fail" and "No configuration or deployment request was sent" in res["msg"], res
        eth_review_assert_no_writes(c)

    def test_deleted_policy_entries_are_ignored_and_the_direct_port_is_accepted(self):
        c = eth_review_ctrl()
        c.policies_extra = [dict(OVERLAY_PROFILE, deleted=True)]
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res

    def test_measured_direct_port_control(self):
        c = eth_review_ctrl()
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        # The policy list is also read by the pre-existing breakout path, so its presence proves
        # nothing alone; the policy-list authority is proven by the read_failure/overlay cases.

    @pytest.mark.parametrize("kind", ["null", "missing_source", "multiple_direct"])
    def test_deleted_state_refuses_an_ambiguous_pvlan_port(self, kind):
        c = eth_review_ctrl()
        c.summary[IF7] = copy.deepcopy(SUMMARY_DEFECTS[kind])
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")
        assert status == "fail"
        eth_review_assert_no_writes(c)

    def test_overridden_refuses_an_ambiguous_unlisted_pvlan_port(self):
        c = eth_review_ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary[IF8] = copy.deepcopy(SUMMARY_DEFECTS["missing_source"])
        status, res = run(c, KEEP_2211, state="overridden")
        assert status == "fail"
        eth_review_assert_no_writes(c)

    def test_ambiguous_second_target_stops_a_valid_first(self):
        c = eth_review_ctrl()
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary[IF7] = copy.deepcopy(SUMMARY_DEFECTS["null"])
        status, res = run(c, [pvlan_item(IF8, **ADD_2212), pvlan_item(IF7, **ADD_2212)])
        assert status == "fail"
        eth_review_assert_no_writes(c)


# ===================================================================================== F3
class TestF3RemainingWorkAndConvergence:

    def test_r1_01_converged_before_resend_skips_the_redundant_deploy(self):
        c = eth_review_ctrl()
        c.previews = [measured_preview("G6-M0b"), measured_preview("G6-M0b", "post")]
        status, res = run(c, [pvlan_item(**ADD_2212)], check_deploy=True)
        assert status == "exit", res
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY", "PREVIEW"]
        assert res["pvlan_gate"][-1]["targets"] == {IF7: "converged"}

    def test_r1_05_valid_removal_after_a_blocked_first_attempt(self):
        c = eth_review_ctrl(ETH_REVIEW_TPROM_BOTH)
        c.previews = [preview([])]  # carries no device authority: refused after the intent write
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "fail" and "ALREADY changed" in res["msg"] and deploys(c) == []
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M1")]  # MEASURED: device still has 2212, intent has 2211 only
        before = len(c.calls)
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "exit", res
        later = list(c.calls[before:])
        assert not [x for x in later if x[1].endswith(MODIFY)] and len([x for x in later if x[1].endswith(DEPLOY)]) == 1

    def test_failed_gate_rerun_for_a_submode_change(self):
        c = eth_review_ctrl(TRANSITIONS["TS1"]["pre_nv"])
        c.previews = [preview([])]
        assert run(c, TSEC_2212, state="replaced")[0] == "fail"
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("TS1")]
        status, res = run(c, TSEC_2212, state="replaced")
        assert status == "exit", res
        assert len(deploys(c)) == 1

    def test_deploy_false_then_deploy_true(self):
        c = eth_review_ctrl()
        assert run(c, [pvlan_item(deploy=False, **ADD_2212)])[0] == "exit"
        assert c.order() == ["MODIFY"]
        c.next_invocation()
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("G6-M0b")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        assert c.order() == ["MODIFY", "PREVIEW", "DEPLOY"]

    def test_complete_convergence_sends_no_deploy(self):
        c = eth_review_ctrl(ETH_REVIEW_TPROM_BOTH)
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}  # stale summary; device already converged
        c.previews = [measured_preview("G6-M0b", "post")]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "exit", res
        assert deploys(c) == [] and c.requests("POST", MODIFY) == []

    def test_partial_convergence_deploys_only_the_remaining_target(self):
        c = eth_review_ctrl(ETH_REVIEW_TPROM_BOTH)
        c.detail[IF8] = {"policy": PVLAN, "nvPairs": pvlan_nv("G6-M0a", ifname=IF8)}
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        run7, exp7 = authority("G6-M0b", "post", IF7)
        run8, exp8 = authority("G6-M0b", "pre", IF8)
        lines = [l.replace("ethernet1/7", "ethernet1/8") for l in pending("G6-M0b")]
        c.previews = [preview(lines, running=run7 + run8, expected=exp7 + exp8)]
        status, res = run(c, [pvlan_item(IF7, **ADD_2212), pvlan_item(IF8, **ADD_2212)])
        assert status == "exit", res
        sent = [json.loads(x[2]) for x in deploys(c)]
        assert sent == [[{"serialNumber": SERIAL, "ifName": IF8, "fabricName": "test_fabric"}]]

    def test_partial_convergence_keeps_non_pvlan_batch_members(self):
        c = eth_review_ctrl(ETH_REVIEW_TPROM_BOTH)
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.detail[IF8] = {"policy": TRUNK, "nvPairs": copy.deepcopy(FIXTURE["trunk_host_baseline"]["nvPairs"])}
        run7, exp7 = authority("G6-M0b", "post", IF7)
        c.previews = [preview(["interface ethernet1/8", "  description sibling", "configure terminal"], running=run7, expected=exp7)]
        status, res = run(c, [pvlan_item(IF7, **ADD_2212), trunk_item(IF8, description="sibling")])
        assert status == "exit", res
        sent = [json.loads(x[2]) for x in deploys(c)]
        assert sent == [[{"serialNumber": SERIAL, "ifName": IF8, "fabricName": "test_fabric"}]]

    # ---- negative controls
    def test_unexpectedly_empty_initial_preview_is_refused(self):
        running, expected = authority("G6-M0b")
        c = eth_review_ctrl()
        c.previews = [preview([], status="In-Sync", running=running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "is empty but the device differs" in res["msg"] and deploys(c) == []

    def test_wrong_withdrawal_is_refused(self):
        running, expected = authority("G6-M1")
        lines = [l.replace("2210 remove 2212", "2210 remove 2211") for l in pending("G6-M1")]
        c = eth_review_ctrl(ETH_REVIEW_TPROM_BOTH)
        c.previews = [preview(lines, running=running, expected=expected)]
        status, res = run(c, KEEP_2211, state="replaced")
        assert status == "fail" and "unexpected partial removal" in res["msg"] and deploys(c) == []

    def test_stale_controller_expectation_is_refused(self):
        running = authority("G6-M0b")[0]
        stale_expected = authority("G6-M0a")[1]  # the controller still expects the old mapping
        c = eth_review_ctrl()
        c.previews = [preview(pending("G6-M0b"), running=running, expected=stale_expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "disagrees with the intended state" in res["msg"] and deploys(c) == []

    def test_ambiguous_device_authority_is_refused(self):
        running, expected = authority("G6-M0b")
        c = eth_review_ctrl()
        c.previews = [preview(pending("G6-M0b"), running=running + running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "2 running" in res["msg"] and deploys(c) == []

    def test_missing_device_authority_is_refused(self):
        expected = authority("G6-M0b")[1]
        c = eth_review_ctrl()
        c.previews = [preview(pending("G6-M0b"), expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "carries no runningConfig" in res["msg"] and deploys(c) == []

    def test_foreign_pending_is_refused(self):
        running, expected = authority("G6-M0b")
        c = eth_review_ctrl()
        c.previews = [preview(pending("G6-M0b") + ["interface ethernet1/9", "  shutdown"], running=running, expected=expected)]
        status, res = run(c, [pvlan_item(**ADD_2212)])
        assert status == "fail" and "outside this deploy batch" in res["msg"] and deploys(c) == []

    def test_malformed_non_trunk_promiscuous_removal_is_refused_on_redeploy(self):
        # Intent already holds the reduced promiscuous mapping (as left by a partial removal); the device
        # still holds both secondaries. The MEASURED pending carries '22102210 remove 2211'.
        c = eth_review_ctrl(TRANSITIONS["PU3"]["post_nv"])
        c.summary_pre[IF7] = {"complianceStatus": "Out-of-Sync"}
        c.previews = [measured_preview("PU3")]
        status, res = run(
            c, [pvlan_item(pvlan_mode="promiscuous", admin_state=False, pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])], state="replaced"
        )
        assert status == "fail" and "malformed VLAN number" in res["msg"] and deploys(c) == []

    def test_defect_guard_still_blocks_the_intent_write(self):
        c = eth_review_ctrl(pvlan_nv("PU2"))
        status, res = run(c, [pvlan_item(pvlan_mode="promiscuous", pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": "2212"}])], state="replaced")
        assert status == "fail" and "keeps other secondaries is blocked" in res["msg"]
        eth_review_assert_no_writes(c)


# ===================================================================================== F4
class TestF4BulkCapabilityInCommonPreflight:

    @pytest.mark.parametrize("check_mode", [False, True])
    def test_missing_bulk_api_is_diagnosed_in_both_modes_r1_06(self, check_mode):
        c = eth_review_ctrl()
        status, res = run(c, [pvlan_item(**ADD_2212)], check_mode=check_mode, bulk=False)
        assert status == "fail" and "bulk interface update API" in res["msg"]
        assert "No configuration or deployment request was sent" in res["msg"]
        eth_review_assert_no_writes(c)

    def test_invalid_second_object_is_still_reported_first(self):
        c = eth_review_ctrl()
        bad = pvlan_item(IF8, pvlan_mode="trunk promiscuous", pvlan_mapping=[{"primary_vlan": True, "secondary_vlans": "2"}])
        status, res = run(c, [pvlan_item(**ADD_2212), bad], check_mode=True, bulk=False)
        assert status == "fail" and "integer VLAN ID" in res["msg"]
        eth_review_assert_no_writes(c)

    def test_no_pvlan_write_needs_no_capability(self):
        c = eth_review_ctrl(ETH_REVIEW_TPROM_BOTH)
        status, res = run(c, [pvlan_item(**ADD_2212)], check_mode=True, bulk=False)  # in sync: no write planned
        assert status == "exit" and res["changed"] is False


# ===================================================================================== F5
class TestF5ActualResetPayload:

    def test_module_reset_payload_and_its_template_predicted_transition(self):
        c = eth_review_ctrl()
        c.previews = [reset_preview()]  # TEMPLATE-PREDICTED
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")
        assert status == "exit", res
        policy, nv = c.sent_nv()
        assert policy == TRUNK
        assert (nv["BPDUGUARD_ENABLED"], nv["PORTTYPE_FAST_ENABLED"], nv["MTU"], nv["ALLOWED_VLANS"], nv["NATIVE_VLAN"]) == (False, True, "jumbo", "none", "")
        assert (nv["ENABLE_STORM_CONTROL"], nv["STORM_CONTROL_ACTION"]) == (False, "no")

    def test_exact_restoration_fixture_is_not_the_module_reset(self):
        c = eth_review_ctrl()
        c.previews = [measured_preview("G6-MR")]  # MEASURED exact restoration (BPDUGUARD 'no')
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")
        assert status == "fail" and "disagrees with the intended state" in res["msg"]
        assert "spanning-tree bpduguard disable" in res["msg"] and deploys(c) == []

    def test_blocked_reset_is_not_reported_as_a_deletion(self):
        running, expected = authority("G6-MR")
        lines = pending("G6-MR")[:-1] + ["  ptp", "configure terminal"]
        c = eth_review_ctrl()
        c.previews = [preview(lines, running=running, expected=expected + ["  spanning-tree bpduguard disable"])]
        status, res = run(c, [{"name": IF7, "switch": ["10.0.0.1"]}], state="deleted")
        assert status == "fail" and "ALREADY changed" in res["msg"] and deploys(c) == []

    @pytest.mark.parametrize("check_mode", [False, True])
    def test_unmodeled_destination_is_refused_before_the_write(self, check_mode):
        c = eth_review_ctrl()
        status, res = run(c, [trunk_item(IF7, admin_state=False, speed="10Gb")], state="replaced", check_mode=check_mode)
        assert status == "fail" and "not covered by the CLI model" in res["msg"]
        eth_review_assert_no_writes(c)


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_e2_units.py
# Helper-level supplements (they do not replace the real-main cases in test_pvlan_ethernet_input.py).
#
# assess_target is replayed on every MEASURED discovery preview that carries device authority: before the deploy each accepted
# transition must be deployable and the partial promiscuous removals refused; after the deploy every converged read must be
# recognised as converged; every repeat read is converged.
# ====================================================================================================
def entry(phase):
    return {"runningConfig": phase["running_stanza"], "expectedConfig": phase["expected_stanza"]}


def body(phase):
    return P.split_blocks(phase["pendingConfig"])[0].get("ethernet1/7", [])


@pytest.mark.parametrize("case", sorted(TRANSITIONS))
def test_measured_pre_deploy_decision(case):
    t = TRANSITIONS[case]
    desired = P.render(t["post_policy"], t["post_nv"])
    decision, problems = P.assess_target(body(DEVICE[case]["pre"]), entry(DEVICE[case]["pre"]), "Ethernet1/7", desired)
    assert decision == ("refuse" if t["expect"] == "reject" else "deploy"), problems


@pytest.mark.parametrize("case", sorted(c for c in TRANSITIONS if "post" in DEVICE[c] and c != "PU3"))
def test_measured_post_deploy_read_is_converged(case):
    t = TRANSITIONS[case]
    desired = P.render(t["post_policy"], t["post_nv"])
    phase = DEVICE[case]["post"]
    assert phase["status"] == "In-Sync" and phase["pendingConfig"] == []
    assert P.assess_target([], entry(phase), "Ethernet1/7", desired) == ("converged", [])


def test_failed_pu3_deploy_is_not_converged_afterwards():
    t = TRANSITIONS["PU3"]
    decision, _problems = P.assess_target(body(DEVICE["PU3"]["post"]), entry(DEVICE["PU3"]["post"]), "Ethernet1/7", P.render(t["post_policy"], t["post_nv"]))
    assert decision == "refuse"


@pytest.mark.parametrize("case", sorted(c for c, d in DEVICE.items() if d["kind"] == "repeat"))
def test_measured_repeat_read_is_converged_with_the_device_state(case):
    phase = DEVICE[case]["pre"]
    assert phase["pendingConfig"] == [] and phase["status"] == "In-Sync"
    device = P.cli_model(P.interface_stanza(phase["running_stanza"], "Ethernet1/7")[1])
    controller = P.cli_model(P.interface_stanza(phase["expected_stanza"], "Ethernet1/7")[1])
    assert P.same_state(device, controller)


def test_cli_model_restores_nxos_defaults():
    m = P.cli_model(["mtu 9216", "switchport mode trunk", "switchport trunk allowed vlan none"])
    assert {"switchport", "no shutdown"} <= m.scalars and m.list_kind is None
    m = P.cli_model(["shutdown", "switchport mode private-vlan trunk promiscuous", "switchport private-vlan mapping trunk 2210 2211-2212"])
    assert m.list_kind == "trunk promiscuous" and m.pairs == {(2210, 2211), (2210, 2212)} and "no shutdown" not in m.scalars


def test_trunk_host_render_follows_the_installed_template():
    nv = {
        "ALLOWED_VLANS": "none",
        "MTU": "jumbo",
        "BPDUGUARD_ENABLED": False,
        "PORTTYPE_FAST_ENABLED": True,
        "ADMIN_STATE": False,
        "NATIVE_VLAN": "",
        "STORM_CONTROL_ACTION": "no",
        "ENABLE_STORM_CONTROL": False,
        "FEC": "auto",
    }
    m = P.render("int_trunk_host", nv)
    assert m.modeled and m.scalars == {
        "switchport",
        "switchport mode trunk",
        "switchport trunk allowed vlan none",
        "mtu 9216",
        "spanning-tree bpduguard disable",
        "spanning-tree port type edge trunk",
        "shutdown",
    }
    for unmodeled in ({"SPEED": "10Gb"}, {"STORM_CONTROL_BCAST_LEVEL_PERCENT": "50"}, {"ENABLE_NETFLOW": "true"}, {"ALLOWED_VLANS": ""}):
        assert not P.render("int_trunk_host", dict(nv, **unmodeled)).modeled


ITEMS = [{"serialNumber": SERIAL, "ifName": "Ethernet1/7"}]


def test_deploy_outcome_accepts_only_evidenced_bodies():
    assert P.deploy_outcome(ok(copy.deepcopy(FIXTURE["deploy_success"])), ITEMS) == ([], False)  # MEASURED
    assert P.deploy_outcome(ok([{"reportItemType": "WARNING", "message": "No Commands to execute"}]), ITEMS) == ([], True)
    rejected = [
        {"RETURN_CODE": 500, "DATA": FIXTURE["deploy_500"]["data"]},
        ok({"reportItemType": "ERROR", "message": "x"}),
        ok({}),
        ok({"message": "Interface deployed successfully", "value": []}),
        ok({"message": "Interface deployed successfully", "value": [{"serialNumber": SERIAL, "IfName": "Ethernet1/8"}]}),
        ok({"message": "Something else", "value": [{"serialNumber": SERIAL, "IfName": "Ethernet1/7"}]}),
        ok([{"reportItemType": "ERROR", "message": "x"}]),
        ok([]),
        ok("text"),
        None,
    ]
    for resp in rejected:
        problems, benign = P.deploy_outcome(resp, ITEMS)
        assert problems and not benign, resp


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_cmds_text.py
# PVLAN Ethernet `cmds` given as text, as NAC renders `freeform_config` (`cmds: |2-` + `default('')`).
#
# Real main() through the PVLAN harness; the NAC fragment is rendered with Jinja2 and parsed as YAML. NOT LIVE TESTED.
# ====================================================================================================
NAC_FRAGMENT = "profile:\n    cmds: |2-\n      {{ interface['freeform_config'] | default('') | indent(6, false) }}\n"
CMDS_TEXT_HOST_A11 = pvlan_nv("H3a")
ASSOC = [{"primary_vlan": 2210, "secondary_vlan": 2211}]
FF_1 = "no autostate"
FF_2 = "logging event port link-status"


def nac_cmds(**interface):
    """The value NAC hands to the module for `freeform_config` (absent when the keyword is not given)."""
    rendered = jinja2.Environment().from_string(NAC_FRAGMENT).render(interface=interface)
    return yaml.safe_load(rendered)["profile"]["cmds"]


def cmds_text_ctrl(nv, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv)}
    return c


def host_item(cmds, deploy=False, ifname=IF7):
    return pvlan_item(ifname, deploy=deploy, pvlan_mode="host", admin_state=False, pvlan_association=copy.deepcopy(ASSOC), cmds=cmds)


def regular_item(mode, cmds, ifname=IF8):
    return {"name": ifname, "type": "eth", "switch": [SWITCH_IP], "deploy": False, "profile": {"mode": mode, "cmds": cmds}}


def assert_refused_before_any_write(c, status, res, fragment):
    assert status == "fail", res
    assert fragment in res["msg"], res["msg"]
    assert "No change was sent" in res["msg"]
    assert c.mutating() == [] and c.requests(mark=PREVIEW_MARK) == []


# ------------------------------------------------------------------ the renderer boundary
def test_r_nac_fragment_renders_text_for_scalar_omitted_and_empty():
    assert nac_cmds(freeform_config=FF_1) == FF_1
    assert nac_cmds() == ""
    assert nac_cmds(freeform_config="") == ""
    assert nac_cmds(freeform_config=FF_1 + "\n" + FF_2) == FF_1 + "\n" + FF_2


# ------------------------------------------------------------------ PVLAN Ethernet accepts the rendered text (real main())
@pytest.mark.parametrize(
    "freeform, conf",
    [
        ({"freeform_config": FF_1}, FF_1),
        ({}, ""),
        ({"freeform_config": ""}, ""),
        ({"freeform_config": FF_1 + "\n" + FF_2}, FF_1 + "\n" + FF_2),
    ],
    ids=["scalar", "omitted", "empty", "multiline"],
)
def test_r_pvlan_host_accepts_the_nac_text_and_sends_it_as_conf(freeform, conf):
    c = cmds_text_ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(nac_cmds(**freeform))])
    assert status == "exit", res
    policy, nv = c.sent_nv()
    assert policy == PVLAN and nv["PVLAN_MODE"] == "host"
    assert nv["CONF"] == conf


@pytest.mark.parametrize("cmds, conf", [([FF_1], FF_1), ([], ""), ([FF_1, FF_2], FF_1 + "\n" + FF_2)], ids=["one", "empty", "two"])
def test_r_pvlan_host_list_control_is_unchanged(cmds, conf):
    c = cmds_text_ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(cmds)])
    assert status == "exit", res
    assert c.sent_nv()[1]["CONF"] == conf


# ------------------------------------------------------------------ parity with the regular Ethernet modes (reference, same text)
@pytest.mark.parametrize("mode", ["trunk", "access"])
@pytest.mark.parametrize(
    "freeform, conf",
    [({"freeform_config": FF_1}, FF_1), ({}, ""), ({"freeform_config": FF_1 + "\n" + FF_2}, FF_1 + "\n" + FF_2)],
    ids=["scalar", "omitted", "multiline"],
)
def test_r_regular_ethernet_sends_the_same_conf_for_the_same_text(mode, freeform, conf):
    c = cmds_text_ctrl(trunk_host_nv(IF8), TRUNK, IF8)
    status, res = run(c, [regular_item(mode, nac_cmds(**freeform))])
    assert status == "exit", res
    sent = c.sent_nv(IF8)
    if sent is None:  # trunk -> trunk with '' against a stored '' is no change: nothing is sent
        assert mode == "trunk" and conf == "" and trunk_host_nv(IF8).get("CONF", "") == ""
    else:
        assert sent[1]["CONF"] == conf


def test_r_regular_path_splits_a_comma_which_pvlan_refuses_instead_of_guessing():
    text = "logging event port link-status, trunk-status"
    c = cmds_text_ctrl(trunk_host_nv(IF8), TRUNK, IF8)
    status, res = run(c, [regular_item("trunk", text)])
    assert status == "exit", res
    assert c.sent_nv(IF8)[1]["CONF"] == "logging event port link-status\n trunk-status"  # the regular conversion, recorded as reference
    c = cmds_text_ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(text)])
    assert_refused_before_any_write(c, status, res, "must not contain a comma")


# ------------------------------------------------------------------ structured-command protection on every line
@pytest.mark.parametrize(
    "cmds",
    [
        FF_1 + "\nswitchport mode trunk",
        FF_1 + "\n  no switchport",
        FF_1 + "\nswitchport private-vlan host-association 2210 2212",
        [FF_1 + "\nswitchport mode trunk"],
        [FF_1, "switchport mode trunk"],
        "switchport mode trunk",
    ],
    ids=["text-line2", "text-line2-no-indented", "text-line2-private-vlan", "list-entry-line2", "list-second-entry", "text-line1"],
)
def test_r_a_structured_command_on_any_line_is_refused_before_any_write(cmds):
    c = cmds_text_ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(cmds)])
    assert_refused_before_any_write(c, status, res, "must not manage private-vlan or switchport")


@pytest.mark.parametrize("cmds", [5, {"line": FF_1}, True, [FF_1, 7], [{"x": 1}]], ids=["int", "dict", "bool", "list-int", "list-dict"])
def test_r_non_text_values_stay_refused(cmds):
    c = cmds_text_ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [host_item(cmds)])
    assert_refused_before_any_write(c, status, res, "cmds must be a list of strings")


# ------------------------------------------------------------------ lifecycle: merged keeps, replaced follows the text, repeat is a no-op
@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_r_repeat_of_the_same_text_sends_nothing(state):
    c = cmds_text_ctrl(dict(CMDS_TEXT_HOST_A11, CONF=FF_1))
    status, res = run(c, [host_item(nac_cmds(freeform_config=FF_1))], state=state)
    assert status == "exit" and res["changed"] is False, res
    assert c.mutating() == []


def test_r_omitted_freeform_under_merged_keeps_the_stored_commands():
    c = cmds_text_ctrl(dict(CMDS_TEXT_HOST_A11, CONF=FF_1))
    status, res = run(c, [host_item(nac_cmds())], state="merged")
    assert status == "exit" and res["changed"] is False, res
    assert c.mutating() == []


def test_r_omitted_freeform_under_replaced_clears_them_like_the_regular_path():
    c = cmds_text_ctrl(dict(CMDS_TEXT_HOST_A11, CONF=FF_1))
    status, res = run(c, [host_item(nac_cmds())], state="replaced")
    assert status == "exit" and res["changed"] is True, res
    assert c.sent_nv()[1]["CONF"] == ""


def test_r_merged_text_appends_only_new_lines():
    c = cmds_text_ctrl(dict(CMDS_TEXT_HOST_A11, CONF=FF_1))
    status, res = run(c, [host_item(nac_cmds(freeform_config=FF_1 + "\n" + FF_2))], state="merged")
    assert status == "exit" and res["changed"] is True, res
    assert c.sent_nv()[1]["CONF"] == FF_1 + "\n" + FF_2


# ------------------------------------------------------------------ the helper itself
@pytest.mark.parametrize(
    "value, lines",
    [
        ("", []),
        (FF_1, [FF_1]),
        (FF_1 + "\n", [FF_1]),
        (FF_1 + "\r\n" + FF_2, [FF_1, FF_2]),
        (FF_1 + "\n\n" + FF_2, [FF_1, "", FF_2]),
        ("  " + FF_1, ["  " + FF_1]),
        ([FF_1, FF_2], [FF_1, FF_2]),
        ([FF_1 + "\n" + FF_2], [FF_1, FF_2]),
        ([""], [""]),
        ([], []),
        ("a, b", None),
        (5, None),
        ([1], None),
    ],
)
def test_r_cmds_lines(value, lines):
    assert P.cmds_lines(value) == lines


@pytest.mark.parametrize(
    "value, conf",
    [(FF_1, FF_1), (FF_1 + "\n", FF_1), (FF_1 + "\r\n" + FF_2 + "\n", FF_1 + "\n" + FF_2), ([FF_1 + "\n"], FF_1), ("", "")],
    ids=["text", "text-trailing-break", "text-crlf", "list-entry-trailing-break", "empty"],
)
def test_r_companion_wire_sends_the_lines_never_the_characters_or_a_trailing_break(value, conf):
    assert P.companion_wire("cmds", value) == conf


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_singleton_range.py
# SINGLETON-RANGE: a single-value inclusive VLAN range "N-N" in a PVLAN profile is the VLAN N.
#
# NaC's convert_ranges macro renders `secondary_vlans: [{from: 2212, to: 2212}]` (and trunk allowed VLANs) as "2212-2212"; the shared
# validator used to refuse it as "not ascending". Now:
#   * interface_pvlan.vlan_set accepts N-N as [N] and still refuses descending, repeated (also "2212,2212-2212"), overlapping, out-of-range
#     and malformed input;
#   * dcnm_interface collapses N-N to N in the raw PVLAN profile (allowed_vlans, peer1/peer2_allowed_vlans, pvlan_mapping secondary_vlans)
#     before validation, so the payload and the comparison are exactly those of N - the controller's own form - and an unchanged repeat
#     written with N-N writes nothing.
# Real main() through the existing Ethernet / port-channel / vPC harnesses; only the controller boundary is faked.
# ====================================================================================================
# ================================================================== the shared parser
@pytest.mark.parametrize("text, expected", [
    ("2212-2212", [2212]),
    ("2212", [2212]),
    ("2212-2213", [2212, 2213]),
    ("2210-2211,2214-2214", [2210, 2211, 2214]),
    ("1-1", [1]),
    ("4094-4094", [4094]),
    ("1", [1]),
    ("4094", [4094]),
    (" 2212 - 2212 ", [2212]),
])
def test_vlan_set_accepts_a_single_value_range_as_one_vlan(text, expected):
    assert P.vlan_set(text, "secondary_vlans") == expected


@pytest.mark.parametrize("text, needle", [
    ("2213-2212", "not ascending"),
    ("2212,2212-2212", "repeats VLAN 2212"),
    ("2212-2212,2212", "repeats VLAN 2212"),
    ("2210-2212,2211-2211", "repeats VLAN 2211"),
    ("2212-2212,2212-2212", "repeats VLAN 2212"),
    ("4095-4095", "outside 1-4094"),
    ("4094-4095", "outside 1-4094"),
    ("0-0", "is not a VLAN list"),
    ("2212-", "is not a VLAN list"),
    ("-2212", "is not a VLAN list"),
    ("2212--2212", "is not a VLAN list"),
    ("02212-02212", "is not a VLAN list"),
    ("a-a", "is not a VLAN list"),
    ("", "is not a VLAN list"),
    ("2212,,2213", "is not a VLAN list"),
])
def test_vlan_set_keeps_refusing_invalid_input(text, needle):
    with pytest.raises(P.PvlanError) as exc:
        P.vlan_set(text, "secondary_vlans")
    assert needle in str(exc.value)


@pytest.mark.parametrize("text, expected", [
    ("2212-2212", "2212"),
    ("2210-2212,2214-2214", "2210-2212,2214"),
    (" 2212 - 2212 ", "2212"),
    ("2213-2212", "2213-2212"),          # descending: left for the validator to refuse
    ("2212,2212-2212", "2212,2212"),     # duplicate stays a duplicate
    ("0-0", "0-0"),                      # malformed: untouched
    ("4095-4095", "4095"),               # collapsed like any N-N; 4095 is then refused by the validator (outside 1-4094)
    ("none", "none"),
    ("", ""),
    (2212, 2212),                        # not a string: untouched
])
def test_collapse_changes_only_well_formed_single_value_ranges(text, expected):
    assert P.collapse_single_value_ranges(text) == expected


def test_normalize_profile_touches_only_the_vlan_lists():
    profile = {"mode": "pvlan", "pvlan_mode": "trunk promiscuous", "native_vlan": "2301",
               "allowed_vlans": "2301-2301", "peer1_allowed_vlans": "10-10,20", "peer2_allowed_vlans": 5,
               "pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212-2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412-2413"}]}
    before = copy.deepcopy(profile)
    changed = P.normalize_single_value_ranges(profile)
    assert changed == ["allowed_vlans", "peer1_allowed_vlans", "pvlan_mapping[0].secondary_vlans"]
    assert profile["allowed_vlans"] == "2301" and profile["peer1_allowed_vlans"] == "10,20" and profile["peer2_allowed_vlans"] == 5
    assert profile["pvlan_mapping"] == [{"primary_vlan": 2210, "secondary_vlans": "2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412-2413"}]
    assert dict((k, v) for k, v in profile.items() if k not in ("allowed_vlans", "peer1_allowed_vlans", "pvlan_mapping")) == \
        dict((k, v) for k, v in before.items() if k not in ("allowed_vlans", "peer1_allowed_vlans", "pvlan_mapping"))


@pytest.mark.parametrize("secondaries, needle", [("4095-4095", "outside 1-4094"), ("2213-2212", "not ascending"),
                                                 ("2212,2212-2212", "repeats VLAN 2212"), ("2211-2213,2212-2212", "repeats VLAN 2212")])
def test_module_still_refuses_invalid_single_value_input_before_any_write(secondaries, needle):
    c = ctrl(trunk_host_nv(), TRUNK)
    status, res = run(c, [eth_tprom(secondaries, "2301")])
    assert status == "fail" and needle in res["msg"], res.get("msg")
    assert_no_writes(c)


def test_requested_pairs_of_a_single_value_range_equal_those_of_the_vlan():
    assert P.requested_pairs("pvlan_mapping", [{"primary_vlan": 2210, "secondary_vlans": "2212-2212"}]) == \
        P.requested_pairs("pvlan_mapping", [{"primary_vlan": 2210, "secondary_vlans": "2212"}]) == [(2210, 2212)]


# ================================================================== Ethernet PVLAN (real main, measured G6-M0a)
def eth_tprom(secondaries, allowed, **kw):
    return pvlan_item(pvlan_mode="trunk promiscuous", admin_state=False,
                      pvlan_mapping=[{"primary_vlan": 2210, "secondary_vlans": secondaries}], native_vlan="2301", allowed_vlans=allowed, **kw)


def test_ethernet_single_value_ranges_send_the_same_payload_as_the_vlans():
    sent = []
    for secondaries, allowed in (("2211", "2301"), ("2211-2211", "2301-2301")):
        c = ctrl(trunk_host_nv(), TRUNK)
        c.previews = [measured_preview("G6-M0a")]
        status, res = run(c, [eth_tprom(secondaries, allowed)])
        assert status == "exit" and res["changed"] is True, res.get("msg")
        policy, nv = c.sent_nv()
        assert policy == PVLAN
        sent.append(nv)
    assert sent[0] == sent[1]
    assert sent[1]["MAPPING_LIST"] == '{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"}]}' and sent[1]["PVLAN_ALLOWED_VLANS"] == "2301"


@pytest.mark.parametrize("secondaries, allowed", [("2211", "2301"), ("2211-2211", "2301-2301")])
def test_ethernet_unchanged_repeat_written_with_single_value_ranges_writes_nothing(secondaries, allowed):
    c = ctrl(TPROM_A11)
    status, res = run(c, [eth_tprom(secondaries, allowed, deploy=False)], state="replaced")
    assert status == "exit" and res["changed"] is False, res.get("msg")
    assert_no_writes(c)


# ================================================================== regular port-channel (real main, battery creation profile)
def po_create(mode, profile):
    _profile, lines = G5.CASES[mode]
    ctrl = G5.new_ctrl(mode)
    ctrl.previews = [G5.creation_preview(mode, lines)]
    status, result = run(ctrl, [G5.item(mode, **profile)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    body = json.loads(ctrl.creates()[0][2])
    return (body[0] if isinstance(body, list) else body)["interfaces"][0]["nvPairs"]


@pytest.mark.parametrize("mode, singleton", [
    ("promiscuous", {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212-2212"}]}),
    ("trunk promiscuous", {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2211-2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412-2412"}],
                           "native_vlan": "2301", "allowed_vlans": "2301-2301"}),
])
def test_port_channel_single_value_ranges_send_the_same_payload_as_the_vlans(mode, singleton):
    reference = po_create(mode, G5.CASES[mode][0])
    candidate = po_create(mode, singleton)
    assert candidate == reference


# ================================================================== vPC (real main, synthetic submode seed)
def vpc_singleton_item(mode):
    if mode == E1.P_:
        extra = {"pvlan_mapping": [{"primary_vlan": r["primary_vlan"], "secondary_vlans": "-".join([r["secondary_vlans"]] * 2)}
                                   if "-" not in r["secondary_vlans"] and "," not in r["secondary_vlans"] else r for r in E1.MAP_P]}
    else:
        extra = {"pvlan_mapping": [{"primary_vlan": r["primary_vlan"], "secondary_vlans": "-".join([r["secondary_vlans"]] * 2)}
                                   if "-" not in r["secondary_vlans"] and "," not in r["secondary_vlans"] else r for r in E1.MAP_TP]}
        extra.update(dict((k, "-".join([v] * 2) if isinstance(v, str) and v.isdigit() and "allowed" in k else v) for k, v in E1.TRUNK_FIELDS.items()))
    return E1.item(mode, **extra)


@pytest.mark.parametrize("mode", [E1.P_, E1.TP])
def test_vpc_single_value_ranges_send_the_same_parent_payload_as_the_vlans(mode):
    sent = []
    for build in (E1.item, vpc_singleton_item):
        ctrl = E1.baseline_ctrl(mode)
        E1.create_previews(ctrl, mode)
        status, result = run_vpc(ctrl, [build(mode)], state="merged")
        assert status == "exit" and result["changed"] is True, result.get("msg")
        sent.append([json.loads(c[2]) for c in ctrl.calls if c[0] in ("POST", "PUT") and c[1].endswith("/globalInterface")])
    assert sent[0] == sent[1] and sent[0]


@pytest.mark.parametrize("mode", [E1.P_, E1.TP])
def test_vpc_unchanged_repeat_written_with_single_value_ranges_writes_nothing(mode):
    ctrl = E1.seeded_ctrl(mode)
    E1.converged_previews(ctrl, mode)
    status, result = run_vpc(ctrl, [vpc_singleton_item(mode)], state="merged")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == []


def test_the_singleton_item_really_carries_n_n_values():
    """Guard on the test data itself: the vPC singleton items must contain an N-N token (else the vPC rows would prove nothing)."""
    for mode in (E1.P_, E1.TP):
        text = json.dumps(vpc_singleton_item(mode)["profile"])
        assert any("%s-%s" % (v, v) in text for v in ("2212", "2211", "2412", "2301", "2302"))


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_units.py
# Helper-level supplements for native Ethernet PVLAN (do not replace the real-main cases).
#
# The measured-transition test replays every G5/G6 discovery pending through the pre-deploy
# validator with its real before/after readbacks: the 46 transitions the controller and device
# accepted must pass, and the two non-trunk partial removals (the measured deploy 500, and its sibling) must not.
# ====================================================================================================
@pytest.mark.parametrize("case", sorted(TRANSITIONS))
def test_measured_transition_is_classified_as_measured(case):
    t = TRANSITIONS[case]
    blocks, global_lines = P.split_blocks(t["pending"])
    problems = P.validate_transition(blocks.get("ethernet1/7", []), P.render(t["pre_policy"], t["pre_nv"]), P.render(t["post_policy"], t["post_nv"]))
    assert global_lines == []
    if t["expect"] == "accept":
        assert problems == [], problems
    else:
        assert any("malformed VLAN number" in p for p in problems)


def test_measured_counts():
    expect = [t["expect"] for t in FIXTURE["transitions"]]
    assert (expect.count("accept"), expect.count("reject")) == (46, 2)


@pytest.mark.parametrize(
    "raw,pairs",
    [
        ("", []),
        ('{"MAPPING_LIST":[]}', []),
        ('{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"},{"P_VLAN":2210,"S_VLAN":"2212"}]}', [(2210, 2211), (2210, 2212)]),
        ('{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211-2212"}]}', [(2210, 2211), (2210, 2212)]),
        ("{'MAPPING_LIST': [{'P_VLAN': '2210', 'S_VLAN': '2211'}]}", [(2210, 2211)]),
    ],
)
def test_have_wire_forms(raw, pairs):
    assert P.pairs_from_wire(raw, "MAPPING_LIST") == pairs


@pytest.mark.parametrize(
    "raw",
    [
        None,
        5,
        "x",
        '{"OTHER":[]}',
        '{"MAPPING_LIST":{}}',
        '{"MAPPING_LIST":[{"S_VLAN":"1"}]}',
        '{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"},{"P_VLAN":"2210","S_VLAN":"2211"}]}',
        '{"MAPPING_LIST":[{"P_VLAN":"5000","S_VLAN":"2211"}]}',
    ],
)
def test_malformed_have_wire_raises(raw):
    with pytest.raises(P.PvlanError):
        P.pairs_from_wire(raw, "MAPPING_LIST")


def test_canonical_wire_is_one_sorted_scalar_row_per_pair():
    assert (
        P.pairs_to_wire("MAPPING_LIST", [(2210, 2212), (2210, 2211)])
        == '{"MAPPING_LIST":[{"P_VLAN":"2210","S_VLAN":"2211"},{"P_VLAN":"2210","S_VLAN":"2212"}]}'
    )
    assert P.pairs_to_wire("ASSOCIATION_LIST", []) == '{"ASSOCIATION_LIST":[]}'


def test_allowed_and_native_equality_keep_none_and_unset_distinct():
    assert P.allowed_equal("2301,2302", "2302,2301") and P.allowed_equal("10-12", "10,11,12")
    assert not P.allowed_equal("", "none") and not P.allowed_equal("none", "1")
    assert not P.native_equal("1", "") and P.native_equal("2301", 2301)


def test_secondary_type_from_measured_network_records():
    nets = FIXTURE["networks"]
    assert P.classify_secondary(nets, 2212) == ("isolated", None)
    assert P.classify_secondary(nets, 2211) == ("community", None)
    assert P.classify_secondary(nets, 2210)[0] is None  # the primary is not a secondary
    assert P.classify_secondary(nets, 4000)[0] is None


def test_template_declarations_cover_every_sent_nvpair():
    declared = P.template_declared_names("##template variables\n" + FIXTURE["template_variables"])
    sent = set(P.reconcile("replaced", {"pvlan_mode": "trunk promiscuous"}, "Ethernet1/7", None, None)["nv"])
    assert sent <= declared, sent - declared


@pytest.mark.parametrize(
    "have,want,blocked",
    [
        ([(2210, 2211), (2210, 2212)], [(2210, 2212)], True),
        ([(2210, 2211), (2210, 2212)], [(2210, 2211), (2210, 2213)], True),
        ([(2210, 2211)], [(2210, 2211), (2210, 2212)], False),
        ([(2210, 2211), (2210, 2212)], [], False),
        ([(2210, 2211)], [(2210, 2211)], False),
    ],
)
def test_promiscuous_partial_removal_predicate(have, want, blocked):
    assert P.promiscuous_partial_removal("promiscuous", "promiscuous", have, want) is blocked
    assert P.promiscuous_partial_removal("trunk promiscuous", "trunk promiscuous", have, want) is False
