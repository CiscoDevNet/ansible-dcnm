"""VPC-HOST-E1-OFFLINE: pure tests of the vPC PVLAN host helpers (no controller, no transport).

NOT LIVE TESTED. Contract labels: [SRC] installed templates captured 2026-10-07 (HOST n / POVPC n = their bodies), [SYN] a synthetic
fixture written by hand, [UNK] only the first live case (L1) can tell. These tests verify OUR code against those, never the controller.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

SN1, SN2 = "FDO00000001", "FDO00000002"
PAIR = SN1 + "~" + SN2
VPC = "vPC10"
M1, M2 = "Ethernet1/7", "Ethernet1/8"
ASSOC = [{"primary_vlan": 2210, "secondary_vlan": 2212}]


def raw(**kw):
    out = {
        "mode": "pvlan",
        "pvlan_mode": "host",
        "peer1_members": [M1],
        "peer2_members": [M2],
        "peer1_pcid": 10,
        "peer2_pcid": 10,
        "admin_state": False,
        "pvlan_association": ASSOC,
    }
    out.update(kw)
    return out


def legs_of(r=None, order=(SN1, SN2)):
    return P.vpc_pair_view(r or raw(), PAIR, list(order))


# ---------------------------------------------------------------- scope: refusals decided from the RAW profile
@pytest.mark.parametrize(
    "mutation, needle",
    [
        # VPC-MODES-E1: the other submodes are implemented; each refuses the list (and fields) its template does not show.
        (lambda r: r.update(pvlan_mode="promiscuous"), "pvlan_association is not valid for pvlan_mode 'promiscuous'"),
        (lambda r: r.update(pvlan_mode="trunk promiscuous"), "pvlan_association is not valid for pvlan_mode 'trunk promiscuous'"),
        (lambda r: r.update(pvlan_mode="trunk secondary", pvlan_mapping=[{"primary_vlan": 1, "secondary_vlans": "2"}]),
         "pvlan_mapping is not valid for pvlan_mode 'trunk secondary'"),
        (lambda r: r.update(pvlan_mode="bogus"), "pvlan_mode must be one of"),
        (lambda r: r.update(peer1_members=[M1, "Ethernet1/9"]), "exactly one member per peer"),
        (lambda r: r.update(peer2_members=[]), "exactly one member per peer"),
        (lambda r: r.update(peer1_members=["Port-channel5"]), "one physical Ethernet"),
        (lambda r: r.update(peer1_pcid=11), "must equal the vPC id"),
        (lambda r: r.update(peer2_pcid=True), "must equal the vPC id"),
        (lambda r: r.pop("peer2_pcid"), "peer2_pcid is required"),
        (lambda r: r.update(pvlan_association=[]), "empty pvlan_association"),
        (lambda r: r.update(peer1_cmds=["x"]), "not implemented for a vPC"),
        (lambda r: r.update(pvlan_mapping=[{"primary_vlan": 1, "secondary_vlans": "2"}]), "pvlan_mapping is not valid for pvlan_mode 'host'"),
        (lambda r: r.update(native_vlan="5"), "not implemented for a vPC"),
        (lambda r: r.update(pc_mode="bogus"), "pc_mode must be one of"),
        (lambda r: r.update(peer1_description=""), "peer1_description must be a single-line"),
        (lambda r: r.update(admin_state="no"), "admin_state must be a boolean"),
        (lambda r: r.update(peer1_description=None), "must not be null"),
    ],
)
def test_scope_refusals_come_from_the_raw_profile(mutation, needle):
    r = raw()
    mutation(r)
    reasons = P.vpc_not_implemented(r, VPC)
    assert any(needle in x for x in reasons), reasons


def test_the_in_scope_profile_has_no_reason_and_the_name_is_checked():
    assert P.vpc_not_implemented(raw(), VPC) == []
    assert any("vPC<1-9999>" in x for x in P.vpc_not_implemented(raw(), "port-channel10"))
    assert P.vpc_id("vpc10") == "10" and P.vpc_id("vPC0") is None and P.vpc_id("Po10") is None


# ---------------------------------------------------------------- identity: every datum stays bound to ITS serial
def test_pair_view_binds_each_peer_to_its_serial_in_the_controllers_order():
    legs = legs_of()
    assert [(leg["serial"], leg["member"], leg["index"]) for leg in legs] == [(SN1, M1, 0), (SN2, M2, 1)]


def test_reversed_playbook_switches_keep_the_serial_and_give_the_same_intent():
    normal = P.vpc_host_nvpairs(raw(), VPC, legs_of())
    # peer1_* now belong to the FIRST playbook switch, which is the controller's SECOND serial
    swapped_raw = raw(peer1_members=[M2], peer2_members=[M1], peer1_description="two", peer2_description="one")
    swapped = P.vpc_host_nvpairs(swapped_raw, VPC, legs_of(swapped_raw, order=(SN2, SN1)))
    plain = raw(peer1_description="one", peer2_description="two")
    expected = P.vpc_host_nvpairs(plain, VPC, legs_of(plain))
    assert swapped == expected
    assert normal["PEER1_MEMBER_INTERFACES"] == M1 and normal["PEER2_MEMBER_INTERFACES"] == M2
    assert swapped["PEER1_MEMBER_INTERFACES"] == M1 and swapped["PEER2_MEMBER_INTERFACES"] == M2


@pytest.mark.parametrize("combined, order", [(PAIR, [SN1]), (PAIR, [SN1, SN1]), (PAIR, [SN1, "FDO0000000X"]), ("FDO00000001", [SN1, SN2]), ("", [SN1, SN2])])
def test_pair_view_refuses_switches_that_are_not_the_pair(combined, order):
    with pytest.raises(P.PvlanError):
        P.vpc_pair_view(raw(), combined, order)


# ---------------------------------------------------------------- payload: complete, exact, typed
EXPECTED_KEYS = {
    "PC_MODE",
    "BPDUGUARD_ENABLED",
    "PORTTYPE_FAST_ENABLED",
    "spanningTreePortType",
    "MTU",
    "SPEED",
    "COPY_DESC",
    "CDP_ENABLE",
    "lldpTransmit",
    "lldpReceive",
    "PORT_DUPLEX_MODE",
    "DISABLE_LACP_SUSPEND",
    "ENABLE_LACP_VPC_CONV",
    "LACP_PORT_PRIO",
    "LACP_RATE",
    "ADMIN_STATE",
    "ENABLE_PFC",
    "ENABLE_QOS",
    "QOS_POLICY",
    "qosStatsSuppressed",
    "QUEUING_POLICY",
    "queuingStats",
    "aclFilter",
    "ENABLE_MIRROR_CONFIG",
    "PVLAN_MODE",
    "MAPPING_LIST",
    "ASSOCIATION_LIST",
    "PEER1_PCID",
    "PEER2_PCID",
    "PEER1_MEMBER_INTERFACES",
    "PEER2_MEMBER_INTERFACES",
    "PEER1_PO_DESC",
    "PEER2_PO_DESC",
    "PEER1_PO_CONF",
    "PEER2_PO_CONF",
    "PEER1_PVLAN_ALLOWED_VLANS",
    "PEER2_PVLAN_ALLOWED_VLANS",
    "PEER1_PVLAN_NATIVE_VLAN",
    "PEER2_PVLAN_NATIVE_VLAN",
}


def test_payload_is_complete_exact_and_typed():
    r = raw(peer1_description="uplink-a", peer2_description="uplink-b")
    nv = P.vpc_host_nvpairs(r, VPC, legs_of(r))
    assert set(nv) == EXPECTED_KEYS and len(nv) == 39, "39 explicit fields + SERIAL_NUMBER/INTF_NAME/PTP owned by the controller = 42 [SRC]"
    assert nv["LACP_PORT_PRIO"] == 32768 and isinstance(nv["LACP_PORT_PRIO"], int)
    assert nv["PEER1_PCID"] == "10" and nv["PEER2_PCID"] == "10" and isinstance(nv["PEER1_PCID"], str)
    assert nv["PEER1_PO_DESC"] == "uplink-a" and nv["PEER2_PO_DESC"] == "uplink-b"
    assert nv["PEER1_PO_CONF"] == "" and nv["PEER2_PO_CONF"] == ""
    assert nv["PEER1_PVLAN_NATIVE_VLAN"] == "" and isinstance(nv["PEER1_PVLAN_NATIVE_VLAN"], str)
    assert nv["PVLAN_MODE"] == "host" and nv["MAPPING_LIST"] == "" and nv["ADMIN_STATE"] == "false" and nv["PC_MODE"] == "active"
    assert P.pairs_from_wire(nv["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(2210, 2212)]
    assert nv["ENABLE_QOS"] == "false" and nv["ENABLE_PFC"] == "false" and nv["aclFilter"] == ""


def test_omitted_fields_are_stated_not_left_to_a_default_that_could_differ_between_create_and_modify():
    nv = P.vpc_host_nvpairs(
        {"pvlan_mode": "host", "peer1_members": [M1], "peer2_members": [M2], "peer1_pcid": 10, "peer2_pcid": 10, "pvlan_association": ASSOC}, VPC, legs_of()
    )
    assert set(nv) == EXPECTED_KEYS and nv["ADMIN_STATE"] == "true" and nv["PEER1_PO_DESC"] == ""


# ---------------------------------------------------------------- reconcile
def have_of(**over):
    nv = P.vpc_host_nvpairs(raw(), VPC, legs_of())
    nv.update({"SERIAL_NUMBER": PAIR, "INTF_NAME": VPC})
    nv.update(over)
    return nv


def test_creation_needs_both_members_and_the_association():
    r = raw()
    r.pop("pvlan_association")
    out = P.reconcile_vpc("merged", r, VPC, legs_of(r), None, None)
    assert out["blocked"] and not out["creates"]
    r = raw()
    r.pop("peer2_members")
    out = P.reconcile_vpc("merged", r, VPC, legs_of(r), None, None)
    assert any("peer1_members and peer2_members" in x for x in out["blocked"])
    out = P.reconcile_vpc("merged", raw(), VPC, legs_of(), None, None)
    assert out["creates"] and out["blocked"] == [] and out["members"] == [M1, M2] and out["ask_legs"] == [0, 1]


def test_an_equal_request_is_a_noop_returning_have_untouched():
    have = have_of()
    out = P.reconcile_vpc("merged", raw(), VPC, legs_of(), P.VPC_HOST_POLICY, have)
    assert out["blocked"] == [] and not out["update"] and not out["creates"] and out["nv"] == have


def test_merged_changes_the_association_and_preserves_every_omitted_field_of_each_peer():
    have = have_of(PEER1_PO_DESC="a", PEER2_PO_DESC="b", MTU="default")
    r = raw(pvlan_association=[{"primary_vlan": 2210, "secondary_vlan": 2213}])
    r.pop("pvlan_association"), r.update(pvlan_association=[{"primary_vlan": 2210, "secondary_vlan": 2212}])
    out = P.reconcile_vpc("merged", r, VPC, legs_of(r), P.VPC_HOST_POLICY, have)
    assert out["blocked"] == [] and not out["update"]
    r = raw(admin_state=True)
    out = P.reconcile_vpc("merged", r, VPC, legs_of(r), P.VPC_HOST_POLICY, have)
    assert out["update"] and out["changed"] == {"ADMIN_STATE": "true"} and out["ask_legs"] == [0, 1]
    assert out["nv"]["PEER1_PO_DESC"] == "a" and out["nv"]["PEER2_PO_DESC"] == "b" and out["nv"]["MTU"] == "default"


def test_replaced_states_the_complete_model():
    have = have_of(PEER1_PO_DESC="a", PEER2_PO_DESC="b")
    out = P.reconcile_vpc("replaced", raw(admin_state=True), VPC, legs_of(), P.VPC_HOST_POLICY, have)
    assert out["update"] and out["nv"]["PEER1_PO_DESC"] == "" and out["nv"]["PEER2_PO_DESC"] == "" and out["nv"]["ADMIN_STATE"] == "true"
    assert set(out["changed"]) == {"ADMIN_STATE", "PEER1_PO_DESC", "PEER2_PO_DESC"} and out["ask_legs"] == [0, 1]


def test_a_change_reaching_one_peer_only_is_refused_not_applied():
    for peer, key in ((1, "peer1_description"), (2, "peer2_description")):
        r = raw(**{key: "only-this-peer"})
        out = P.reconcile_vpc("merged", r, VPC, legs_of(r), P.VPC_HOST_POLICY, have_of())
        assert not out["update"] and any("changes only peer %d" % peer in x for x in out["blocked"]), out
    r = raw(peer1_description="x", peer2_description="y")  # both peers: symmetric, allowed
    out = P.reconcile_vpc("merged", r, VPC, legs_of(r), P.VPC_HOST_POLICY, have_of())
    assert out["update"] and out["ask_legs"] == [0, 1] and out["blocked"] == []


@pytest.mark.parametrize(
    "have_over, needle",
    [
        ({"PVLAN_MODE": "trunk promiscuous"}, "changing pvlan_mode of an existing vPC"),
        ({"PEER2_PCID": "11"}, "differs from the vPC id"),
        ({"PEER2_PO_CONF": "mtu 1500"}, "freeform commands on peer 2"),
        ({"PEER1_MEMBER_INTERFACES": "Ethernet1/7,Ethernet1/9"}, "one explicit member per peer"),
        ({"PEER2_MEMBER_INTERFACES": ""}, "one explicit member per peer"),
        ({"MYSTERY_FIELD": "x"}, "cannot classify"),
    ],
)
def test_existing_vpc_outside_the_contract_is_refused(have_over, needle):
    out = P.reconcile_vpc("merged", raw(), VPC, legs_of(), P.VPC_HOST_POLICY, have_of(**have_over))
    assert any(needle in x for x in out["blocked"]), out["blocked"]


def test_member_change_and_policy_conversion_are_refused():
    r = raw(peer2_members=["Ethernet1/9"])
    out = P.reconcile_vpc("merged", r, VPC, legs_of(r), P.VPC_HOST_POLICY, have_of())
    assert any("changing the member" in x for x in out["blocked"])
    out = P.reconcile_vpc("merged", raw(), VPC, legs_of(), "int_vpc_trunk_host", have_of())
    assert any("converting it" in x for x in out["blocked"])


# ---------------------------------------------------------------- the CLI models of one leg
def test_the_child_po_model_is_the_regular_po_body_plus_the_vpc_line():
    nv = have_of()
    (_po_kind, po), (_member_kind, member) = (
        P.vpc_leg_models(nv, 0, VPC, {"ADMIN_STATE": "false", "DESC": "", "CONF": ""}, False)[0],
        P.vpc_leg_models(nv, 0, VPC, {"ADMIN_STATE": "false", "DESC": "", "CONF": ""}, False)[1],
    )
    model = P.render(P.VPC_PO_POLICY, po)
    assert model.modeled and "vpc 10" in model.scalars and "switchport mode private-vlan host" in model.scalars
    assert "shutdown" in model.scalars and "mtu 9216" in model.scalars and model.pairs == {(2210, 2212)}
    assert po["PRIMARY_INTF"] == VPC and po["PO_ID"] == "port-channel10"
    mm = P.render(P.PO_MEMBER_POLICY, member)
    assert mm.modeled and "channel-group 10 mode active" in mm.scalars and "channel-group 10 force mode active" not in mm.scalars
    assert mm.pairs == {(2210, 2212)} and "mtu 9216" in mm.scalars


@pytest.mark.parametrize(
    "over",
    [
        {"ENABLE_QOS": "true"},
        {"ENABLE_PFC": "true"},
        {"aclFilter": "acl1"},
        {"ENABLE_LACP_VPC_CONV": "true"},
        {"SPEED": "10Gb"},
        {"QUEUING_POLICY": "q"},
        {"PORT_DUPLEX_MODE": "full"},
        {"spanningTreePortType": "network"},
    ],
)
def test_values_outside_the_model_make_the_child_unmodeled(over):
    nv = have_of(**over)
    po = P.vpc_leg_po_nv(nv, 0, VPC)
    assert not P.render(P.VPC_PO_POLICY, po).modeled


def test_cli_change_is_derived_from_the_previous_and_new_models_not_from_the_nvpair_diff():
    old, new = have_of(), have_of(ADMIN_STATE="true")
    member = {"ADMIN_STATE": "false", "DESC": "", "CONF": ""}
    pre = P.vpc_leg_models(old, 0, VPC, member, True)
    assert P.vpc_leg_cli_changes(pre, P.vpc_leg_models(new, 0, VPC, member, True)) is True  # no shutdown on the child Po
    # an nvPair change with NO CLI effect: the COPY_DESC bookkeeping with an empty description renders the same member
    same = have_of(COPY_DESC="true")
    assert P.vpc_leg_cli_changes(pre, P.vpc_leg_models(same, 0, VPC, member, True)) is False


# ---------------------------------------------------------------- the vPC decision from per-leg decisions
@pytest.mark.parametrize(
    "mode, decisions, expected, out",
    [
        ("create", ["deploy", "deploy"], None, "deploy"),
        ("create", ["deploy", "converged"], None, "refuse"),
        ("create", ["converged", "deploy"], None, "refuse"),
        ("create", ["deploy", "refuse"], None, "refuse"),
        ("create", ["refuse", "deploy"], None, "refuse"),
        ("delete", ["deploy", "deploy"], None, "deploy"),
        ("delete", ["converged", "converged"], None, "refuse"),
        ("repeat", ["converged", "converged"], None, "converged"),
        ("repeat", ["deploy", "deploy"], None, "deploy"),
        ("repeat", ["converged", "deploy"], None, "refuse"),
        ("repeat", ["deploy", "converged"], None, "refuse"),
        ("update", ["deploy", "deploy"], ["deploy", "deploy"], "deploy"),
        ("update", ["deploy", "converged"], ["deploy", "converged"], "deploy"),  # a leg with no CLI change is LEGITIMATELY converged
        ("update", ["deploy", "converged"], ["deploy", "deploy"], "refuse"),  # converged where the models predict a change
        ("update", ["deploy", "deploy"], ["deploy", "converged"], "refuse"),  # pending where the models predict none
        ("update", ["converged", "converged"], ["converged", "converged"], "converged"),
        ("update", ["deploy", "deploy"], None, "refuse"),
        ("create", ["deploy"], None, "refuse"),
        ("create", ["deploy", "deploy", "deploy"], None, "refuse"),
        ("create", ["deploy", None], None, "refuse"),
        ("bogus", ["deploy", "deploy"], None, "refuse"),
    ],
)
def test_the_vpc_decision_is_never_one_leg(mode, decisions, expected, out):
    decision, problems = P.vpc_combine(mode, decisions, expected)
    assert decision == out and (problems == [] or decision == "refuse")


# ---------------------------------------------------------------- the answer to the parent CREATE
def item(kind, entity=PAIR + "~" + VPC):
    return {"reportItemType": kind, "message": "m", "entity": entity}


@pytest.mark.parametrize(
    "resp, cls",
    [
        ({"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {}}, "accepted"),
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [item("SUCCESS")]}, "accepted"),  # [SYN] provisional shape
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [item("SUCCESS", PAIR + ":" + VPC)]}, "accepted"),  # the second admitted entity form
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [item("SUCCESS"), item("SUCCESS", SN1 + "~port-channel10")]}, "accepted"),
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [item("ERROR")]}, "failed"),
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [item("SUCCESS"), item("ERROR", SN2 + "~port-channel10")]}, "failed"),
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [item("SUCCESS", "OTHER~" + VPC)]}, "unknown"),  # an alien identity
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [item("SUCCESS", SN1 + "~port-channel10")]}, "unknown"),  # a child only, not the parent
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [item("WARNING")]}, "unknown"),
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": []}, "unknown"),
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": {"x": 1}}, "unknown"),
        ({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": ["not a dict"]}, "unknown"),
        ({"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}, "failed"),
        ({"RETURN_CODE": 200, "MESSAGE": "Something else", "DATA": {}}, "failed"),
        (None, "unknown"),
        ("garbage", "unknown"),
    ],
)
def test_response_classes_never_pass_an_error_or_an_unknown_shape(resp, cls):
    assert P.vpc_response_class(resp, PAIR, VPC) == cls


# ---------------------------------------------------------------- residue after a deletion (per peer)
def pol(entity, template, source="", deleted=False, etype="INTERFACE"):
    return {"entityName": entity, "templateName": template, "source": source, "deleted": deleted, "entityType": etype}


def baseline_member_nv():
    return {"ADMIN_STATE": "false", "CONF": ""}


CLEAN = [pol("Ethernet1/7", "int_trunk_host"), pol("Ethernet1/9", "int_trunk_host"), pol("loopback0", "int_loopback")]


@pytest.mark.parametrize(
    "policies, mnv, needle",
    [
        (CLEAN, baseline_member_nv(), None),  # D1 the released member's own policy is NOT residue
        (CLEAN + [pol("Ethernet1/7", "int_trunk_host", deleted=True)], baseline_member_nv(), None),  # deleted entries are not live
        (CLEAN + [pol("Ethernet1/7", "int_eth", source="vPC10")], baseline_member_nv(), "owned by the removed vPC"),  # D2 a child still claims it
        (CLEAN + [pol("port-channel10", "int_vpc_pvlan_po", source="vPC10")], baseline_member_nv(), "owned by the removed vPC"),
        (CLEAN + [pol("port-channel10", "int_port_channel_trunk_host")], baseline_member_nv(), "for the removed port-channel"),  # D3
        (CLEAN + [pol("vPC10", "int_vpc_pvlan_host")], baseline_member_nv(), "for the removed vPC"),
        ([pol("Ethernet1/7", "int_port_channel_pvlan_member")], baseline_member_nv(), "does not hold exactly one direct"),  # D4 still PVLAN
        (CLEAN + [pol("Ethernet1/7", "Config_Profile", source="OVERLAY")], baseline_member_nv(), "does not hold exactly one direct"),  # D5 overlay
        (CLEAN, {"ADMIN_STATE": "true", "CONF": ""}, "not administratively down"),  # D6
        (CLEAN, {"ADMIN_STATE": "false", "CONF": "mtu 1500"}, "freeform CONF"),
        ([pol("Ethernet1/7", "int_access_host")], baseline_member_nv(), "does not hold exactly one direct"),  # D9 another template
        ([pol("Ethernet1/7", "int_trunk_host", source="someone")], baseline_member_nv(), "does not hold exactly one direct"),
        ([], baseline_member_nv(), "does not hold exactly one direct"),  # the member has no policy at all
        (CLEAN + [pol("Ethernet1/9", "int_eth", source="port-channel10")], baseline_member_nv(), "claimed by the removed port-channel"),
    ],
)
def test_residue_distinguishes_the_valid_member_baseline_from_what_the_vpc_left(policies, mnv, needle):
    reasons = P.vpc_leg_residue(policies, VPC, "port-channel10", M1, mnv)
    if needle is None:
        assert reasons == []
    else:
        assert any(needle in x for x in reasons), reasons


def test_the_old_blanket_rule_would_have_rejected_the_valid_baseline_and_the_new_rule_does_not():
    blanket = [p for p in CLEAN if p["entityName"].lower() == "ethernet1/7"]
    assert blanket, "G2 6.4 called ANY policy whose entityName is the member residue: that would reject the baseline"
    assert P.vpc_leg_residue(CLEAN, VPC, "port-channel10", M1, baseline_member_nv()) == []


def test_child_differences_detect_a_leg_that_does_not_follow_its_parent():
    po = P.vpc_leg_po_nv(have_of(), 0, VPC)
    assert P.vpc_child_differences(dict(po), po) == []
    assert "ASSOCIATION_LIST" in P.vpc_child_differences(dict(po, ASSOCIATION_LIST=P.pairs_to_wire("ASSOCIATION_LIST", [(2210, 2299)])), po)
    assert "ADMIN_STATE" in P.vpc_child_differences(dict(po, ADMIN_STATE="true"), po)
    assert P.vpc_child_differences(None, po) == ["nvPairs"]
    assert "PRIMARY_INTF" in P.vpc_child_differences(dict(po, PRIMARY_INTF="vPC11"), po)


# ---------------------------------------------------------------- Po and Ethernet tables untouched
def test_po_and_ethernet_vocabularies_are_unchanged_by_the_vpc_tables():
    assert P.PO_VOCABULARY_POLICIES == ("int_port_channel_pvlan_host", "int_port_channel_pvlan_member")
    assert P.VOCABULARY_POLICIES == ("int_pvlan_host", "int_trunk_host")
    assert P.VPC_VOCABULARY_POLICIES == ("int_vpc_pvlan_po",)
    assert P.render(P.PO_HOST_POLICY, {}).modeled is False and P.render("int_vpc_pvlan_host", {}).modeled is False
    voc = P.transition_vocabulary((P.VPC_PO_POLICY, {}), (P.VPC_PO_POLICY, {}))
    assert voc.owns("vpc 10") and voc.owns("switchport private-vlan host-association 2210 2212") and not voc.owns("vpc orphan-port suspend 5x")
    assert not P.transition_vocabulary((P.PO_HOST_POLICY, {}), (P.PO_MEMBER_POLICY, {})).owns("vpc 10")


def test_shared_validator_limit_shutdown_to_no_shutdown_cannot_be_satisfied_even_by_the_ideal_pending():
    # FINDING (shared engine, unchanged here): `no shutdown` adds a line and withdraws `shutdown` at once, but validate_transition counts a
    # withdrawal only for a line that starts with "no " AND is not itself an owned post line. An admin_state flip therefore refuses at the gate.
    child_down, child_up = have_of(ADMIN_STATE="false"), have_of(ADMIN_STATE="true")
    pre, post = P.render(P.VPC_PO_POLICY, P.vpc_leg_po_nv(child_down, 0, VPC)), P.render(P.VPC_PO_POLICY, P.vpc_leg_po_nv(child_up, 0, VPC))
    problems = P.vpc_transition_problems(pre, post)
    assert any("withdrawal of 'shutdown' is absent" in x for x in problems), problems
    po_nv = P.po_host_nvpairs({"pvlan_mode": "host", "pvlan_association": ASSOC, "members": [M1], "admin_state": False}, "Port-channel10")
    pre_po, post_po = P.render(P.PO_HOST_POLICY, po_nv), P.render(P.PO_HOST_POLICY, dict(po_nv, ADMIN_STATE="true"))
    body = ["no shutdown"]
    assert P.validate_transition(body, pre_po, post_po), "the regular Po model has the same limit (not changed by this generation)"
    # a transition the validator CAN satisfy: a new description
    d_pre = P.render(P.VPC_PO_POLICY, P.vpc_leg_po_nv(have_of(), 0, VPC))
    d_post = P.render(P.VPC_PO_POLICY, P.vpc_leg_po_nv(have_of(PEER1_PO_DESC="x"), 0, VPC))
    assert P.vpc_transition_problems(d_pre, d_post) == []
