"""Native Ethernet PVLAN (int_pvlan_host): input, wire, state semantics and before-write gate.

Every case drives the real main() through test_dcnm_intf_pvlan_harness (external boundary
mocked only). Case IDs E01-E08 refer to the design's offline acceptance matrix.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

import pytest

from .test_dcnm_intf_pvlan_harness import (
    IF7,
    IF8,
    PREVIEW_MARK,
    PVLAN,
    TRANSITIONS,
    TRUNK,
    FakeController,
    measured_preview,
    pvlan_item,
    pvlan_nv,
    run,
    trunk_host_nv,
    trunk_item,
)

TPROM_A11 = pvlan_nv("G6-M0a")
TPROM_BOTH = pvlan_nv("G6-M0b")
HOST_A11 = pvlan_nv("H3a")
HOST_A12 = pvlan_nv("H3b")
PROM_A11 = pvlan_nv("PU1")
PROM_BOTH = pvlan_nv("PU2")
TSEC_A12 = pvlan_nv("TS1")


def mapping(*secondaries):
    return [{"primary_vlan": 2210, "secondary_vlans": ",".join(str(s) for s in secondaries)}]


def assoc(secondary, primary=2210):
    return [{"primary_vlan": primary, "secondary_vlan": secondary}]


def ctrl(nv, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv)}
    return c


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


def assert_no_writes(c):
    assert c.mutating() == [], c.mutating()
    assert c.requests(mark=PREVIEW_MARK) == []


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
