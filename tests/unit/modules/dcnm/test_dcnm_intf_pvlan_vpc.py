"""VPC-HOST-E1-OFFLINE: focused tests of the vPC PVLAN host lifecycle (create, repeat, symmetric update, delete) over a PAIR of switches.

NOT LIVE TESTED. Real main(); only the external boundary is mocked (see test_dcnm_intf_pvlan_vpc_harness for the labelling of every fixture:
source contract / SYNTHETIC fixture / future live measurement). Every `run_vpc` builds a NEW module instance, so repetition, update and
deletion run WITHOUT any memory of the invocation that created the vPC.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_harness import TRUNK, ok, preview, trunk_host_nv
from .test_dcnm_intf_pvlan_vpc_harness import (
    release_only,
    IP1,
    IP2,
    M1,
    M2,
    PAIR,
    PO_MEMBER,
    PRIMARY,
    SECONDARY,
    SN1,
    SN2,
    VPC,
    VPC_HOST,
    VpcController,
    baseline_ctrl,
    converged_preview,
    converged_previews,
    create_pending,
    create_preview,
    create_previews,
    created_ctrl,
    delete_previews,
    member_after,
    pc_mode_preview,
    description_preview,
    po_stanza,
    run_vpc,
    update_preview,
    vpc_del_item,
    vpc_item,
)

NEW = (PRIMARY, 2213)


def created_via_module():
    """The first M1: create through the module itself (used where the test needs the module's own payload to be what is stored)."""
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit" and result["changed"] is True, result
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl


# ================================================================== creation
def test_creation_route_payload_order_and_both_peers_validated_before_the_single_deploy():
    ctrl = baseline_ctrl()
    create_previews(ctrl, descs=("uplink-a", "uplink-b"))
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="uplink-a", peer2_description="uplink-b")])
    assert status == "exit" and result["changed"] is True, result
    assert len(ctrl.creates()) == 1 and ctrl.modifies() == [] and len(ctrl.deploys()) == 1
    body = json.loads(ctrl.creates()[0][2])
    payload = body[0] if isinstance(body, list) else body
    assert payload["policy"] == VPC_HOST and payload["interfaces"][0]["serialNumber"] == PAIR and payload["interfaces"][0]["ifName"] == VPC
    nv = payload["interfaces"][0]["nvPairs"]
    assert nv["PEER1_MEMBER_INTERFACES"] == M1 and nv["PEER2_MEMBER_INTERFACES"] == M2
    assert nv["PEER1_PO_DESC"] == "uplink-a" and nv["PEER2_PO_DESC"] == "uplink-b" and nv["ADMIN_STATE"] == "false"
    assert nv["LACP_PORT_PRIO"] == 32768 and nv["PEER1_PCID"] == "10" and nv["PEER2_PCID"] == "10" and nv["PEER1_PO_CONF"] == ""
    assert P.pairs_from_wire(nv["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(PRIMARY, SECONDARY)]
    # BOTH previews (one per peer, each with ITS serial) are read after the intent exists and BEFORE the one deploy
    assert sorted(ctrl.previews_asked()) == [SN1, SN2]
    order = ctrl.order()
    assert order == ["PREVIEW", "PREVIEW", "DEPLOY"], order
    assert json.loads(ctrl.deploys()[0][2]) == [{"serialNumber": PAIR, "ifName": VPC, "fabricName": "test_fabric"}]
    assert [g["peer"] for g in result["pvlan_gate"]] == [1, 2] and all(g["targets"][VPC] == "deploy" for g in result["pvlan_gate"])
    # the members are never written by the module: they appear only through the parent
    assert ctrl.requests("POST", "/rest/interface/modify") == []
    # the post-deploy readback reads BOTH peers' policy lists (success on one peer is not success of the vPC)
    reads = [c[1].rsplit("/", 1)[1] for c in ctrl.calls if "/control/policies/switches/" in c[1]]
    assert reads.count(SN1) >= 2 and reads.count(SN2) >= 2


def test_creation_with_the_playbook_switches_in_the_other_order_sends_the_same_intent():
    ctrl_a, ctrl_b = baseline_ctrl(), baseline_ctrl()
    create_previews(ctrl_a, descs=("one", "two"))
    create_previews(ctrl_b, descs=("one", "two"))
    assert run_vpc(ctrl_a, [vpc_item(peer1_description="one", peer2_description="two")])[0] == "exit"
    # peer1_* belong to the FIRST switch, now the controller's second serial: the data keep their serial
    status, result = run_vpc(ctrl_b, [vpc_item(switches=[IP2, IP1], peer1_members=[M2], peer2_members=[M1], peer1_description="two", peer2_description="one")])
    assert status == "exit", result

    def sent(c):
        body = json.loads(c.creates()[0][2])
        body = body[0] if isinstance(body, list) else body
        return body["interfaces"][0]["nvPairs"]

    assert sent(ctrl_a) == sent(ctrl_b)
    assert sent(ctrl_b)["PEER1_MEMBER_INTERFACES"] == M1 and sent(ctrl_b)["PEER2_PO_DESC"] == "two"


def test_creation_without_deploy_sends_no_preview_and_no_deploy():
    ctrl = baseline_ctrl()
    status, result = run_vpc(ctrl, [vpc_item(deploy=False)])
    assert status == "exit" and len(ctrl.creates()) == 1 and ctrl.deploys() == [] and ctrl.order() == []


def test_a_vpc_trunk_item_still_takes_the_unchanged_generic_path():
    ctrl = baseline_ctrl()
    item = {
        "name": "vpc20",
        "type": "vpc",
        "switch": [IP1, IP2],
        "deploy": False,
        "profile": {"mode": "trunk", "peer1_members": ["Ethernet1/20"], "peer2_members": ["Ethernet1/21"], "pc_mode": "active"},
    }
    status, result = run_vpc(ctrl, [item])
    assert status == "exit", result
    body = json.loads(ctrl.creates()[0][2])
    payload = body[0] if isinstance(body, list) else body
    assert payload["policy"] == "int_vpc_trunk_host" and "PEER1_PVLAN" not in json.dumps(payload)
    assert ctrl.previews_asked() == [] and ctrl.deploys() == []


# ================================================================== scope: everything outside the first delivery is refused BEFORE a write
@pytest.mark.parametrize(
    "profile, needle",
    [
        # VPC-MODES-E1: a promiscuous creation needs its mapping; trunk secondary from the harness trunk member is the known incident.
        ({"pvlan_mode": "promiscuous", "pvlan_association": None}, "pvlan_mapping is required"),
        ({"pvlan_mode": "trunk secondary"}, "Known incident pending engineering"),
        ({"peer2_members": [M2, "Ethernet1/9"]}, "exactly one member per peer"),
        ({"peer1_pcid": 11}, "must equal the vPC id"),
        ({"peer1_pcid": None}, "must not be null"),
        ({"pvlan_association": []}, "empty pvlan_association"),
        ({"peer1_cmds": ["no shutdown"]}, "not implemented for a vPC"),
        ({"native_vlan": "5"}, "not implemented for a vPC"),
    ],
)
def test_out_of_scope_requests_are_refused_before_any_write(profile, needle):
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    item = vpc_item()
    for k, v in profile.items():
        if v is None and k != "peer1_pcid":
            item["profile"].pop(k, None)
        else:
            item["profile"][k] = v
    status, result = run_vpc(ctrl, [item])
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.previews_asked() == []


@pytest.mark.parametrize(
    "kw, needle",
    [
        ({"state": "overridden"}, "not implemented for a vPC in mode 'pvlan'"),
        ({"check_mode": True}, "refused in check mode"),
        ({"version": (11, "11.5.4")}, "not a supported vPC mode"),
    ],
)
def test_states_versions_and_check_mode_not_implemented(kw, needle):
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()], **kw)
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert ctrl.writes() == []


@pytest.mark.parametrize("switches", [[IP1], [IP1, IP1]])
def test_the_two_switches_of_the_pair_are_required(switches):
    ctrl = baseline_ctrl()
    status, result = run_vpc(ctrl, [vpc_item(switches=switches)])
    assert status == "fail" and "exactly the two switches" in result["msg"] and ctrl.writes() == []


# ================================================================== a problem on the SECOND peer only: zero writes
def _peer2_member_owned_by_an_overlay(c):
    c.policies_extra[SN2] = [
        {
            "entityName": M2,
            "entityType": "INTERFACE",
            "templateName": "Config_Profile",
            "source": "OVERLAY",
            "deleted": False,
            "policyId": "OVL-1",
            "serialNumber": SN2,
        }
    ]


def _peer2_member_up(c):
    c.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = "true"


def _peer2_member_has_conf(c):
    c.nodes[SN2][M2]["nvPairs"]["CONF"] = "mtu 1500"


def _peer2_member_already_in_a_port_channel(c):
    c.nodes[SN2][M2] = {"policy": PO_MEMBER, "source": "port-channel5", "nvPairs": {"PO_ID": "port-channel5", "ADMIN_STATE": "false"}}


def _peer2_member_absent(c):
    c.nodes[SN2].pop(M2)


def _peer2_child_po_already_exists(c):
    c.nodes[SN2]["port-channel10"] = {"policy": "int_port_channel_trunk_host", "nvPairs": {"PO_ID": "port-channel10"}}


def _peer2_stray_policy_of_the_vpc(c):
    c.policies_extra[SN2] = [
        {
            "entityName": "Ethernet1/50",
            "entityType": "INTERFACE",
            "templateName": "int_eth",
            "source": VPC,
            "deleted": False,
            "policyId": "STRAY",
            "serialNumber": SN2,
        }
    ]


def _peer2_policy_list_unreadable(c):
    c.read_failures = {"/control/policies/switches/" + SN2}


def _peer2_summary_unreadable(c):
    c.read_failures = {"/rest/interface/detail?serialNumber=" + SN2}


def _peer2_detail_unreadable(c):
    c.read_failures = {"/rest/interface?serialNumber=" + SN2}


@pytest.mark.parametrize(
    "prep, needle",
    [
        (_peer2_member_owned_by_an_overlay, "live policies for it"),
        (_peer2_member_up, "not administratively down"),
        (_peer2_member_has_conf, "freeform CONF"),
        (_peer2_member_already_in_a_port_channel, "already a port-channel member"),
        (_peer2_member_absent, "not an existing physical interface"),
        (_peer2_child_po_already_exists, "already holds an intent for port-channel10"),
        (_peer2_stray_policy_of_the_vpc, "live policy(ies) for this absent vPC"),
        (_peer2_policy_list_unreadable, "could not be read authoritatively"),
        (_peer2_summary_unreadable, "could not be read authoritatively"),
        (_peer2_detail_unreadable, "could not be read authoritatively"),
    ],
)
def test_a_problem_only_on_the_second_peer_refuses_the_whole_vpc_with_zero_writes(prep, needle):
    ctrl = baseline_ctrl()
    prep(ctrl)
    create_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert SN2 in result["msg"], "the refusal names the peer that caused it"
    assert ctrl.writes() == [] and ctrl.previews_asked() == [], "nothing is written or deployed because of ONE peer"


def test_a_problem_only_on_the_first_peer_is_not_lost_when_the_second_peer_is_read_afterwards():
    # Reading the second peer's summary drops part of the shared per-switch cache (the pair is "covered" by both queries), so each leg is judged
    # from its OWN snapshot. A summary-only stray on peer 1 (no detail, no policy) must still refuse the creation.
    ctrl = baseline_ctrl()
    ctrl.summary_extra[SN1] = [
        {
            "ifName": "port-channel10",
            "serialNo": SN1,
            "fabricName": "test_fabric",
            "ifType": "INTERFACE_PORT_CHANNEL",
            "isPhysical": "False",
            "deletable": "True",
            "editAllowed": "True",
            "markDeleted": "False",
            "alias": "",
            "deleteReason": None,
            "complianceStatus": "In-Sync",
            "underlayPolicies": [],
            "interfaces": [{"nvPairs": {}}],
        }
    ]
    create_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and "the interface summary lists port-channel10" in result["msg"] and SN1 in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.previews_asked() == []


def test_the_same_port_cannot_be_assigned_to_two_vpcs_of_one_playbook():
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    other = vpc_item(name="vpc11", peer1_pcid=11, peer2_pcid=11, peer1_members=[M1], peer2_members=["Ethernet1/9"])
    status, result = run_vpc(ctrl, [vpc_item(), other])
    assert status == "fail" and "also assigns it to" in result["msg"] and ctrl.writes() == []


# ================================================================== the gate: both peers, one decision
def test_a_forbidden_preview_on_the_second_peer_stops_every_deploy_and_names_the_peer():
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    foreign = create_pending(M2) + ["interface Ethernet1/40", "  shutdown"]
    ctrl.vpc_previews[SN2] = [preview(foreign, serial=SN2, running=[], expected=po_stanza() + member_after(M2))]
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and ctrl.deploys() == [], "peer 1 would deploy; the vPC is not deployed because of peer 2"
    assert "peer 2" in result["msg"] and "ALREADY changed" in result["msg"] and "MAY have changed on one or both peers" in result["msg"]
    assert sorted(ctrl.previews_asked()) == [SN1, SN2], "both peers were judged before the decision"
    assert [g["targets"][VPC] for g in result["pvlan_gate"]] == ["deploy", "refuse"], "the evidence of each peer is kept"


def test_a_forbidden_preview_on_the_second_peer_also_stops_the_deploy_of_an_unrelated_change_in_the_same_batch():
    ctrl = baseline_ctrl()
    nv = trunk_host_nv("Ethernet1/9")
    nv["ADMIN_STATE"] = "false"
    ctrl.nodes[SN1]["Ethernet1/9"] = {"policy": TRUNK, "nvPairs": nv}
    create_previews(ctrl)
    foreign = create_pending(M2) + ["interface Ethernet1/40", "  shutdown"]
    ctrl.vpc_previews[SN2] = [preview(foreign, serial=SN2, running=[], expected=po_stanza() + member_after(M2))]
    unrelated = {
        "name": "eth1/9",
        "type": "eth",
        "switch": [IP1],
        "deploy": True,
        "profile": {"mode": "trunk", "description": "unrelated change", "admin_state": False},
    }
    status, result = run_vpc(ctrl, [vpc_item(), unrelated])
    assert status == "fail" and "peer 2" in result["msg"]
    assert ctrl.deploys() == [], "nothing is deployed: neither the vPC nor the unrelated interface of the same batch"
    assert len(ctrl.creates()) == 1 and (len(ctrl.modifies()) == 1), "both intents were written before the gate (reported, never rolled back)"


def test_a_peer_that_is_already_converged_on_a_new_vpc_is_not_explained_and_nothing_is_deployed():
    ctrl = baseline_ctrl()
    ctrl.vpc_previews[SN1] = [create_preview(SN1, M1)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2)]
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and ctrl.deploys() == [] and "peer 2 is already converged" in result["msg"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda pv: pv["DATA"][0]["expectedConfig"].append("interface port-channel10") or pv,  # a duplicated expected stanza
        lambda pv: pv["DATA"][0].pop("runningConfig") and pv,  # no device authority
        lambda pv: pv["DATA"][0]["expectedConfig"].__setitem__(  # the controller expects something else
            slice(None), [line.replace("2212", "2299") for line in pv["DATA"][0]["expectedConfig"]]
        )
        or pv,
        lambda pv: pv["DATA"][0]["pendingConfig"].append("  speed 10000") or pv,  # an unmodeled command in the pending
        lambda pv: pv["DATA"][0]["pendingConfig"].insert(0, "vlan 99") or pv,  # a global command
    ],
)
def test_every_per_peer_gate_defect_refuses_and_never_deploys(mutate):
    for bad_peer in (SN1, SN2):
        ctrl = baseline_ctrl()
        create_previews(ctrl)
        ctrl.vpc_previews[bad_peer] = [mutate(ctrl.vpc_previews[bad_peer][0])]
        status, result = run_vpc(ctrl, [vpc_item()])
        assert status == "fail" and ctrl.deploys() == [], bad_peer
        assert ("peer 1" in result["msg"]) == (bad_peer == SN1)


def test_a_failed_or_malformed_preview_on_either_peer_never_deploys():
    for bad_peer in (SN1, SN2):
        for bad in ({"RETURN_CODE": 500, "MESSAGE": "boom", "DATA": {}}, ok({}), ok([]), ok([{"switchId": "OTHER", "status": "In-Sync", "pendingConfig": []}])):
            ctrl = baseline_ctrl()
            create_previews(ctrl)
            ctrl.vpc_previews[bad_peer] = [bad]
            status, result = run_vpc(ctrl, [vpc_item()])
            assert len(ctrl.creates()) == 1, "the intent was written; the gate is what refused"
            assert status == "fail" and ctrl.deploys() == [] and sorted(ctrl.previews_asked()) == [SN1, SN2]


# ================================================================== the answer to the create: uncertainty never enables a deploy
def _item(kind, entity):
    return {"reportItemType": kind, "message": "m", "entity": entity}


@pytest.mark.parametrize(
    "resp",
    [
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("ERROR", PAIR + "~" + VPC)]},
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("SUCCESS", PAIR + "~" + VPC), _item("ERROR", SN2 + "~port-channel10")]},
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("SUCCESS", "OTHER~vPC99")]},
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("SUCCESS", SN1 + "~port-channel10")]},
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("WARNING", PAIR + "~" + VPC)]},
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": []},
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": {"unexpected": True}},
        {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}},
    ],
)
def test_an_error_alien_unknown_or_incomplete_answer_to_the_create_never_reaches_a_preview_or_a_deploy(resp):
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    ctrl.create_responses = [resp]
    status, result = run_vpc(ctrl, [vpc_item()])
    assert len(ctrl.creates()) == 1, "the create WAS sent: the failure is the answer to it, not an earlier refusal"
    assert status == "fail" and ctrl.deploys() == [] and ctrl.previews_asked() == []


def test_an_error_answer_is_not_neutralised_by_a_favourable_readback():
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    ctrl.create_responses = [{"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("ERROR", PAIR + "~" + VPC)]}]
    status, result = run_vpc(ctrl, [vpc_item()])
    # the fake applies a 207 to its state: after the ERROR answer the controller really holds the parent and BOTH children (a favourable
    # readback). The ERROR still stops the run before any preview or deploy.
    assert VPC in ctrl.parents and "port-channel10" in ctrl.nodes[SN1] and "port-channel10" in ctrl.nodes[SN2]
    assert len(ctrl.creates()) == 1 and status == "fail" and ctrl.deploys() == [] and ctrl.previews_asked() == []


def test_a_recognised_207_is_accepted_but_success_still_needs_both_peers_read_back():
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    ctrl.create_responses = [{"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("SUCCESS", PAIR + "~" + VPC)]}]  # [SYN] provisional shape
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit" and len(ctrl.deploys()) == 1 and sorted(ctrl.previews_asked()) == [SN1, SN2]
    # ...and the same accepted answer with the child of ONE peer missing afterwards is a failure of the vPC
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    ctrl.create_responses = [{"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("SUCCESS", PAIR + "~" + VPC)]}]
    original_call = VpcController.__call__

    def drop_peer2_child_after_deploy(self, mod, method, path, data=None):
        resp = original_call(self, mod, method, path, data)
        if path.endswith("/rest/globalInterface/deploy"):
            self.nodes[SN2].pop("port-channel10", None)
        return resp

    VpcController.__call__ = drop_peer2_child_after_deploy
    try:
        status, result = run_vpc(ctrl, [vpc_item()])
    finally:
        VpcController.__call__ = original_call
    assert status == "fail" and len(ctrl.deploys()) == 1 and "peer 2" in result["msg"], result.get("msg")


@pytest.mark.parametrize(
    "deploy_resp",
    [
        {"RETURN_CODE": 500, "MESSAGE": "boom", "DATA": {}},
        {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"reportItemType": "ERROR", "message": "x"}},
        {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": {"message": "Interface deployed successfully", "value": [{"serialNumber": SN1, "IfName": VPC}]}},
    ],
)
def test_a_failed_or_unrecognised_deploy_answer_fails_and_keeps_the_response(deploy_resp):
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    ctrl.deploy_responses = [deploy_resp]
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1 and result["response"], "the original deploy response is retained"


def test_post_deploy_a_peer_that_is_not_in_sync_fails_the_vpc():
    ctrl = baseline_ctrl()
    create_previews(ctrl)
    ctrl.compliance_by[(SN2, "port-channel10")] = "Out-of-Sync"
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and "peer 2 (%s): child is Out-of-Sync, not In-Sync" % SN2 in result["msg"] and "peer 1 (" not in result["msg"]


def test_post_deploy_children_that_do_not_exist_are_not_assumed():
    ctrl = baseline_ctrl()
    ctrl.children_on_save = False  # [UNK] V3: the first live case measures when the children appear
    create_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1, "after the deploy: a parent without its children is not success"


# ================================================================== repetition (NEW module instance, no memory)
def test_identical_repetition_in_a_new_instance_is_a_noop_that_still_judges_both_peers():
    ctrl = created_via_module()
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit" and result["changed"] is False, result
    assert ctrl.writes() == [] and ctrl.deploys() == []
    assert sorted(ctrl.previews_asked()) == [SN1, SN2], "an unchanged vPC is still read and gated on BOTH peers"


def test_a_vpc_whose_intent_is_saved_but_applied_on_neither_peer_is_not_completed_by_a_repetition():
    ctrl = created_via_module()
    for serial, port in ((SN1, M1), (SN2, M2)):  # both peers lost the association line on the device: both still have pending work
        running = [line for line in po_stanza() if "host-association" not in line] + member_after(port)
        ctrl.vpc_previews[serial] = [
            preview(
                ["interface port-channel10", "  switchport private-vlan host-association %d %d" % (PRIMARY, SECONDARY)],
                serial=serial,
                running=running,
                expected=po_stanza() + member_after(port),
            )
        ]
    # E1 limit (stop and preserve): completing an unapplied vPC is not implemented; its recovery is the deletion
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and "saved but not applied on either peer" in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == []
    # a vPC that was never applied at all (no child port-channel on the device) is not a coherent baseline either
    ctrl = created_via_module()
    ctrl.vpc_previews[SN1] = [create_preview(SN1, M1)]
    ctrl.vpc_previews[SN2] = [create_preview(SN2, M2)]
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and "0 running and 1 expected stanzas" in result["msg"] and ctrl.writes() == []


def test_pre_existing_partial_state_is_refused_before_any_write_on_repeat_and_on_update():
    for config, state in ((vpc_item(), "merged"), (vpc_item(pvlan_association=[{"primary_vlan": PRIMARY, "secondary_vlan": 2213}]), "replaced")):
        ctrl = created_via_module()
        ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1)]
        # peer 2 lost the association line on the device: its pending re-adds it while peer 1 is converged (applied on ONE peer only)
        running = [line for line in po_stanza() if "host-association" not in line] + member_after(M2)
        ctrl.vpc_previews[SN2] = [
            preview(
                ["interface port-channel10", "  switchport private-vlan host-association %d %d" % (PRIMARY, SECONDARY)],
                serial=SN2,
                running=running,
                expected=po_stanza() + member_after(M2),
            )
        ]
        status, result = run_vpc(ctrl, [config], state=state)
        assert status == "fail" and ctrl.writes() == [], result.get("msg")
        assert "pre-existing partial state: peer 1 is converged and peer 2 is deploy" in result["msg"], result["msg"]


def test_a_vpc_whose_second_peer_lost_its_child_is_a_partial_state_not_a_repetition():
    ctrl = created_via_module()
    ctrl.nodes[SN2].pop("port-channel10")
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and ctrl.writes() == [] and "peer 2" in result["msg"].replace(SN2, "peer 2")


def test_a_child_that_does_not_follow_its_parent_is_a_partial_state():
    ctrl = created_via_module()
    ctrl.nodes[SN2]["port-channel10"]["nvPairs"]["ASSOCIATION_LIST"] = P.pairs_to_wire("ASSOCIATION_LIST", [(2210, 2299)])
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and ctrl.writes() == [] and "does not follow the parent" in result["msg"]


def test_a_member_that_stopped_being_the_vpcs_member_is_refused():
    ctrl = created_via_module()
    ctrl.nodes[SN1][M1] = {"policy": TRUNK, "nvPairs": ctrl.nodes[SN1][M1]["nvPairs"]}
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and ctrl.writes() == []


def test_stored_freeform_conf_on_the_second_peer_is_refused_before_any_write():
    for state in ("merged", "replaced"):
        ctrl = created_ctrl()
        ctrl.parents[VPC]["nvPairs"]["PEER2_PO_CONF"] = "mtu 1500"
        converged_previews(ctrl)
        status, result = run_vpc(ctrl, [vpc_item()], state=state)
        assert status == "fail" and "freeform commands on peer 2" in result["msg"] and ctrl.writes() == []


def test_the_second_peers_ownership_is_judged_by_its_own_policy_list():
    ctrl = created_ctrl()
    ctrl.nodes[SN2]["port-channel10"]["source"] = "someone-else"
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and ctrl.writes() == [] and SN2 in result["msg"]


def test_a_foreign_policy_for_the_parent_on_a_peer_list_is_refused():
    ctrl = created_ctrl()
    ctrl.policies_extra[SN2] = [
        {
            "entityName": VPC,
            "entityType": "INTERFACE",
            "templateName": "int_vpc_trunk_host",
            "source": "",
            "deleted": False,
            "policyId": "X",
            "serialNumber": PAIR,
        }
    ]
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and ctrl.writes() == [] and "not a direct int_vpc_pvlan_host" in result["msg"]


def test_the_parent_policy_listed_on_the_peers_does_not_break_a_coherent_vpc():
    ctrl = created_ctrl()
    ctrl.list_parent_policy = True  # [UNK] V2: both listings are accepted; absence of the listing is the other branch (every test above)
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit" and result["changed"] is False


# ================================================================== update: symmetric only, from a coherent baseline
def test_symmetric_update_sends_the_full_set_gates_both_peers_and_reads_both_back():
    ctrl = created_via_module()
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1), update_preview(SN1, M1, (PRIMARY, SECONDARY), NEW)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2), update_preview(SN2, M2, (PRIMARY, SECONDARY), NEW)]
    status, result = run_vpc(ctrl, [vpc_item(pvlan_association=[{"primary_vlan": PRIMARY, "secondary_vlan": 2213}])], state="replaced")
    assert status == "exit" and result["changed"] is True, result
    assert len(ctrl.modifies()) == 1 and ctrl.creates() == [] and len(ctrl.deploys()) == 1
    body = json.loads(ctrl.modifies()[0][2])
    sent = body[0]["interfaces"][0]["nvPairs"]
    assert body[0]["policy"] == VPC_HOST and body[0]["interfaces"][0]["serialNumber"] == PAIR
    assert P.pairs_from_wire(sent["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(PRIMARY, 2213)]
    assert sent["PEER1_MEMBER_INTERFACES"] == M1 and sent["PEER2_MEMBER_INTERFACES"] == M2 and len(sent) >= 39, "the FULL set is sent"
    order = ctrl.order()
    assert order == ["PREVIEW", "PREVIEW", "MODIFY", "PREVIEW", "PREVIEW", "DEPLOY"], "prior state of both peers, then the write, then the gate"
    assert [g["site"] for g in result["pvlan_gate"]] == ["prior", "prior", "deploy", "deploy"]


def test_merged_update_preserves_what_was_omitted_for_each_peer():
    ctrl = created_ctrl(descs=("keep-a", "keep-b"))
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1, desc="keep-a"), pc_mode_preview(SN1, M1, "keep-a")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2, desc="keep-b"), pc_mode_preview(SN2, M2, "keep-b")]
    status, result = run_vpc(ctrl, [vpc_item(pc_mode="passive")], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert sent["PC_MODE"] == "passive", "the requested change"
    assert sent["PEER1_PO_DESC"] == "keep-a" and sent["PEER2_PO_DESC"] == "keep-b", "each peer keeps ITS omitted description"
    assert P.pairs_from_wire(sent["ASSOCIATION_LIST"], "ASSOCIATION_LIST") == [(PRIMARY, SECONDARY)] and sent["PEER1_PCID"] == "10"
    assert sent["ADMIN_STATE"] == "false" and len(ctrl.deploys()) == 1
    assert ctrl.order() == ["PREVIEW", "PREVIEW", "MODIFY", "PREVIEW", "PREVIEW", "DEPLOY"]


def test_an_admin_state_change_is_refused_before_the_intent_changes_because_the_gate_cannot_validate_it():
    # shared-validator limit: `shutdown` <-> `no shutdown` is one line that adds and withdraws at once, so even the IDEAL pending fails
    ctrl = created_ctrl()
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item(admin_state=True)], state="merged")
    assert status == "fail" and "cannot be validated by the pre-deploy gate" in result["msg"] and "shutdown" in result["msg"], result.get("msg")
    assert ctrl.writes() == [] and ctrl.modifies() == []


def test_unilateral_update_is_refused_before_the_modify():
    for key in ("peer1_description", "peer2_description"):
        ctrl = created_ctrl()
        converged_previews(ctrl)
        status, result = run_vpc(ctrl, [vpc_item(**{key: "one-peer-only"})], state="merged")
        assert status == "fail" and "not implemented" in result["msg"] and "changes only peer" in result["msg"], result.get("msg")
        assert ctrl.writes() == [] and ctrl.modifies() == []


def test_update_naming_both_peers_is_symmetric_and_allowed():
    ctrl = created_ctrl()
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1), description_preview(SN1, M1, None, "a")]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2), description_preview(SN2, M2, None, "b")]
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="a", peer2_description="b")], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    sent = json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]
    assert sent["PEER1_PO_DESC"] == "a" and sent["PEER2_PO_DESC"] == "b"
    assert ctrl.nodes[SN1]["port-channel10"]["nvPairs"]["DESC"] == "a" and ctrl.nodes[SN2]["port-channel10"]["nvPairs"]["DESC"] == "b"


def test_symmetric_update_in_check_mode_is_refused_because_the_bulk_capability_cannot_be_verified():
    ctrl = created_ctrl()
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item(peer1_description="a", peer2_description="b")], state="merged", check_mode=True)
    assert status == "fail" and "bulk" in result["msg"] and ctrl.writes() == []


def test_update_whose_second_peer_shows_no_change_is_not_explained_and_is_not_deployed():
    ctrl = created_via_module()
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1), update_preview(SN1, M1, (PRIMARY, SECONDARY), NEW)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2), converged_preview(SN2, M2, NEW)]  # peer 2 already shows the NEW intent applied
    status, result = run_vpc(ctrl, [vpc_item(pvlan_association=[{"primary_vlan": PRIMARY, "secondary_vlan": 2213}])], state="replaced")
    assert status == "fail" and ctrl.deploys() == [] and len(ctrl.modifies()) == 1
    assert "peer 2 shows converged but this update predicts deploy" in result["msg"] and "ALREADY changed" in result["msg"], result["msg"]


@pytest.mark.parametrize(
    "resp",
    [
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("ERROR", PAIR + "~" + VPC)]},
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [_item("SUCCESS", "OTHER~vPC9")]},
        {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": []},
    ],
)
def test_an_uncertain_update_answer_never_reaches_a_gate_or_a_deploy(resp):
    ctrl = created_via_module()
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2)]
    ctrl.modify_responses = [resp]
    status, result = run_vpc(ctrl, [vpc_item(pvlan_association=[{"primary_vlan": PRIMARY, "secondary_vlan": 2213}])], state="replaced")
    assert status == "fail" and ctrl.deploys() == []
    assert ctrl.previews_asked() == [SN1, SN2], "only the PRIOR state of both peers was read; no gate and no deploy after the bad answer"


def test_mode_member_and_pcid_changes_of_an_existing_vpc_are_refused():
    promiscuous = vpc_item(pvlan_mode="promiscuous", pvlan_mapping=[{"primary_vlan": PRIMARY, "secondary_vlans": str(SECONDARY)}])
    promiscuous["profile"].pop("pvlan_association")
    for item, needle in ((vpc_item(peer2_members=["Ethernet1/9"]), "changing the member"), (promiscuous, "changing pvlan_mode of an existing vPC")):
        ctrl = created_ctrl()
        converged_previews(ctrl)
        status, result = run_vpc(ctrl, [item])
        assert status == "fail" and needle in result["msg"] and ctrl.writes() == []


# ================================================================== deletion (NEW instance, no memory of the creation)
def test_deletion_in_a_new_instance_marks_deletes_releases_both_members_down_deploys_and_verifies_both_peers():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and json.loads(ctrl.markdeletes()[0][2]) == [{"ifName": VPC, "serialNumber": PAIR}]
    assert len(ctrl.deploys()) == 1 and [d["ifName"] for d in json.loads(ctrl.deploys()[0][2])] == [VPC]
    # E4 (G4 decision B, MEASURED for a regular Po, INFERRED for a vPC): the controller releases each member ADMIN_STATE "true"; the module sets ONLY
    # ADMIN_STATE false on each, one legacy modify per peer, BEFORE the deploy
    release_only(ctrl)
    assert ctrl.creates() == [] and ctrl.order().count("DEPLOY") == 1
    sent = [json.loads(c[2])[0]["interfaces"][0] for c in ctrl.modifies()]
    assert sorted((i["serialNumber"], i["ifName"]) for i in sent) == sorted([(SN1, M1), (SN2, M2)])
    assert all(len(i["nvPairs"]) >= 40 for i in sent), "the COMPLETE writable nvPairs, not a sparse payload"
    assert [r["member_modify"][:23] for r in result["pvlan_vpc_release"]] == ["ADMIN_STATE true -> fal"] * 2
    assert VPC not in ctrl.parents and "port-channel10" not in ctrl.nodes[SN1] and "port-channel10" not in ctrl.nodes[SN2]
    assert ctrl.nodes[SN1][M1]["policy"] == TRUNK and ctrl.nodes[SN2][M2]["policy"] == TRUNK
    verification = result["pvlan_verification"][VPC]
    assert verification["state"] == "verified" and verification["parent"] == "absent"
    assert verification["peers"] == {SN1: "verified", SN2: "verified"}
    assert sorted(ctrl.previews_asked()) == [SN1, SN2] and [g["targets"][VPC] for g in result["pvlan_gate"]] == ["deploy", "deploy"]


def test_repetition_of_the_deletion_is_a_noop():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    status, first = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and first["pvlan_verification"][VPC]["state"] == "verified"
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is False and ctrl.writes() == []


def test_the_deletion_accepts_a_deleted_vpc_without_any_summary_listing_of_the_parent():
    ctrl = created_ctrl()
    ctrl.vpc_in_summary = False  # [UNK] V0
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified"


def _conf_on_peer2(c):
    c.parents[VPC]["nvPairs"]["PEER2_PO_CONF"] = "mtu 1500"


def _mode_not_host(c):
    c.parents[VPC]["nvPairs"]["PVLAN_MODE"] = "bogus"  # VPC-MODES-E1: the four submodes are deletable; an unknown one is not


def _pcid_differs(c):
    c.parents[VPC]["nvPairs"]["PEER2_PCID"] = "11"


def _two_members_on_peer1(c):
    c.parents[VPC]["nvPairs"]["PEER1_MEMBER_INTERFACES"] = M1 + ",Ethernet1/9"


def _member2_up(c):
    c.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = "true"


def _member2_not_ours(c):
    c.nodes[SN2][M2]["nvPairs"]["PO_ID"] = "port-channel99"


def _child2_missing(c):
    c.nodes[SN2].pop("port-channel10")


def _child2_foreign_policy(c):
    c.nodes[SN2]["port-channel10"]["source"] = "vPC99"


def _policy_list2_unreadable(c):
    c.read_failures = {"/control/policies/switches/" + SN2}


@pytest.mark.parametrize(
    "prep, needle",
    [
        (_conf_on_peer2, "freeform commands on peer 2"),
        (_mode_not_host, "not in a known pvlan_mode"),
        (_pcid_differs, "differs from the vPC id"),
        (_two_members_on_peer1, "exactly one explicit member per peer"),
        (_member2_up, "not administratively down"),
        (_member2_not_ours, "not the member of port-channel10"),
        (_child2_missing, "partial state"),
        (_child2_foreign_policy, "does not hold exactly one"),
        (_policy_list2_unreadable, "partial state"),
    ],
)
def test_deletion_preconditions_judge_the_current_state_of_both_peers_and_refuse_before_any_write(prep, needle):
    ctrl = created_ctrl()
    prep(ctrl)
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert ctrl.writes() == [], "refused before the mark-delete: nothing is deleted, nothing deployed"


@pytest.mark.parametrize(
    "kw, item_kw, needle",
    [
        ({}, {"deploy": False}, "without deploy is not implemented"),
        ({"check_mode": True}, {}, "refused in check mode"),
        ({"fabric_admin": "true"}, {}, "HOST_INTF_ADMIN_STATE"),
    ],
)
def test_deletion_requirements(kw, item_kw, needle):
    ctrl = created_ctrl()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item(**item_kw)], state="deleted", **kw)
    assert status == "fail" and needle in result["msg"] and ctrl.writes() == []


def test_deleting_a_non_pvlan_vpc_is_unchanged():
    ctrl = baseline_ctrl()
    ctrl.parents["vPC30"] = {"policy": "int_vpc_trunk_host", "nvPairs": {"PEER1_PCID": "30", "PEER2_PCID": "30"}}
    item = {"name": "vpc30", "type": "vpc", "switch": [IP1, IP2], "deploy": True}
    status, result = run_vpc(ctrl, [item], state="deleted")
    assert status == "exit" and len(ctrl.markdeletes()) == 1 and ctrl.previews_asked() == [] and ctrl.nodes[SN1][M1]["policy"] == TRUNK


def test_deletion_gate_refuses_when_one_peers_preview_is_not_the_released_state_and_does_not_deploy():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    pv = ctrl.vpc_previews[SN2][0]
    pv["DATA"][0]["expectedConfig"] = [line for line in pv["DATA"][0]["expectedConfig"] if line != "  shutdown"]  # the member would come up
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [] and "ALREADY changed" in result["msg"] and "peer 2" in result["msg"]
    assert len(ctrl.markdeletes()) == 1, "the mark-delete was sent before the gate (as for a regular port-channel): reported, never rolled back"


def test_deletion_gate_refuses_when_the_child_is_still_expected_on_one_peer():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    pv = ctrl.vpc_previews[SN1][0]
    pv["DATA"][0]["expectedConfig"] = po_stanza() + pv["DATA"][0]["expectedConfig"]
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [] and "still holds port-channel10" in result["msg"]


def test_a_valid_released_member_baseline_is_not_residue():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    # after the deletion each member holds exactly ONE direct int_trunk_host policy: that is the contract baseline, not residue
    live = [p for p in ctrl._peer_policies(SN1) if p["entityName"] == M1]
    assert result["pvlan_verification"][VPC]["state"] == "verified", "the verification ran and accepted the baseline"
    assert status == "exit" and [p["templateName"] for p in live] == [TRUNK] and live[0]["source"] == ""


def test_residue_only_on_the_second_peer_stops_the_release_before_the_deploy_and_names_the_partial_state():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    ctrl.policies_extra[SN2] = [
        dict(entityName="Ethernet1/60", entityType="INTERFACE", templateName="int_eth", source=VPC, deleted=False, policyId="RES", serialNumber=SN2)
    ]
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "member release failed while proving the released member before any member write (peer 2)" in result["msg"], result.get("msg")
    assert "live policies still reference the vPC or its child port-channel" in result["msg"]
    # the observable partial state: peer 1's member WAS released and corrected (confirmed), peer 2's was not touched, nothing deployed
    assert "legacy interface/modify of %s on peer 1 ADMIN_STATE false (per-item SUCCESS)" % M1 in result["msg"]
    assert ctrl.deploys() == [] and len(ctrl.markdeletes()) == 1
    release_only(ctrl, count=1)
    assert ctrl.nodes[SN1][M1]["nvPairs"]["ADMIN_STATE"] == "false" and ctrl.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] == "true"
    record = result["pvlan_vpc_release"][-1]
    assert record["peer"] == 2 and record["uncertain_writes"] == [] and len(record["confirmed_writes"]) == 2


class LateResidue(VpcController):
    """A residue that appears only AFTER the deploy (the controller finishes the deletion late): the post-deploy verification must catch it."""

    def __call__(self, mod, method, path, data=None):
        resp = super(LateResidue, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith("/rest/globalInterface/deploy"):
            self.policies_extra[SN2] = [
                dict(entityName="Ethernet1/60", entityType="INTERFACE", templateName="int_eth", source=VPC, deleted=False, policyId="RES", serialNumber=SN2)
            ]
        return resp


def test_residue_only_on_the_second_peer_after_the_deploy_fails_the_verification():
    ctrl = LateResidue().seed_baseline().seed_vpc()
    ctrl.next_invocation()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "release could not be verified on every peer" in result["msg"] and "peer 2" in result["msg"]
    assert "peer 1 (" not in result["msg"] and "peer 2 (%s): a policy owned by the removed vPC" % SN2 in result["msg"]
    assert result["pvlan_verification"][VPC]["state"] == "failed"
    assert result["pvlan_verification"][VPC]["peers"][SN1] == "verified" and result["pvlan_verification"][VPC]["peers"][SN2] != "verified"
    release_only(ctrl)


def test_a_member_still_holding_the_pvlan_policy_after_the_mark_delete_stops_before_any_member_write_and_any_deploy():
    ctrl = created_ctrl()
    ctrl.release_on_delete = False  # the controller leaves int_port_channel_pvlan_member in place on BOTH peers
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "member release failed while proving the released member before any member write (peer 1)" in result["msg"], result.get("msg")
    assert "live policies still reference the vPC or its child port-channel" in result["msg"] and "int_port_channel_pvlan_member/vPC10" in result["msg"]
    assert ctrl.modifies() == [] and ctrl.deploys() == [] and len(ctrl.markdeletes()) == 1, "nothing is written to a member that is still bound"


def test_a_child_policy_still_claiming_a_member_stops_the_release_before_any_write():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    ctrl.policies_extra[SN1] = [
        {"entityName": M1, "entityType": "INTERFACE", "templateName": "int_eth", "source": VPC, "deleted": False, "policyId": "RES", "serialNumber": SN1}
    ]
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "live policies still reference the vPC or its child port-channel" in result["msg"], result.get("msg")
    assert "(peer 1)" in result["msg"], result.get("msg")
    assert ctrl.modifies() == [] and ctrl.deploys() == []


@pytest.mark.parametrize(
    "flaky",
    [
        {SN1: [True] * 40, SN2: [True] * 40},  # every read fails
        {SN1: [False] * 40, SN2: [True] * 40},  # peer 1 always readable, peer 2 never
        {SN1: [True, False] * 20, SN2: [False, True] * 20},  # intermittent, never BOTH peers readable in one attempt
    ],
)
def test_unreadable_state_after_the_deletion_is_never_a_verified_deletion(flaky):
    ctrl = created_ctrl()
    delete_previews(ctrl)
    ctrl.policy_failures = flaky
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "release could not be verified" in result["msg"]
    assert result["pvlan_verification"][VPC]["state"] == "failed"
    release_only(ctrl)
    assert len(ctrl.markdeletes()) == 1


def test_a_deletion_that_is_readable_only_on_a_later_complete_attempt_is_verified_by_that_complete_read():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    ctrl.policy_failures = {SN1: [True, True, False] + [False] * 10, SN2: [True, True, False] + [False] * 10}
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified"


def test_deleting_a_vpc_that_does_not_exist_is_a_noop_next_to_a_real_one():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item(), {"name": "vpc77", "type": "vpc", "switch": [IP1, IP2], "deploy": True}], state="deleted")
    assert status == "exit" and VPC in result["pvlan_verification"]
