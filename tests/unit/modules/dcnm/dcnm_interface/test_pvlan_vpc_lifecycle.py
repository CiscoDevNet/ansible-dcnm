"""vPC PVLAN host lifecycle over a pair of switches and its reconciliation controls."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .helpers.ethernet_controller import TRUNK
from .helpers.ethernet_controller import ok
from .helpers.ethernet_controller import preview
from .helpers.ethernet_controller import trunk_host_nv
from .helpers.vpc_controller import release_only
from .helpers.vpc_controller import IP1
from .helpers.vpc_controller import IP2
from .helpers.vpc_controller import M1
from .helpers.vpc_controller import M2
from .helpers.vpc_controller import PAIR
from .helpers.vpc_controller import PO_MEMBER
from .helpers.vpc_controller import PRIMARY
from .helpers.vpc_controller import SECONDARY
from .helpers.vpc_controller import SN1
from .helpers.vpc_controller import SN2
from .helpers.vpc_controller import VPC
from .helpers.vpc_controller import VPC_HOST
from .helpers.vpc_controller import VpcController
from .helpers.vpc_controller import baseline_ctrl
from .helpers.vpc_controller import converged_preview
from .helpers.vpc_controller import converged_previews
from .helpers.vpc_controller import create_pending
from .helpers.vpc_controller import create_preview
from .helpers.vpc_controller import create_previews
from .helpers.vpc_controller import created_ctrl
from .helpers.vpc_controller import delete_previews
from .helpers.vpc_controller import member_after
from .helpers.vpc_controller import pc_mode_preview
from .helpers.vpc_controller import description_preview
from .helpers.vpc_controller import po_stanza
from .helpers.vpc_controller import run_vpc
from .helpers.vpc_controller import update_preview
from .helpers.vpc_controller import vpc_del_item
from .helpers.vpc_controller import vpc_item
from .helpers.fixture_cases import load_case


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc.py
# Focused tests of the vPC PVLAN host lifecycle (create, repeat, symmetric update, delete) over a PAIR of switches.
#
# NOT LIVE TESTED. Real main(); only the external boundary is mocked (see helpers/vpc_controller for the labelling of every fixture:
# source contract / SYNTHETIC fixture / future live measurement). Every `run_vpc` builds a NEW module instance, so repetition, update and
# deletion run WITHOUT any memory of the invocation that created the vPC.
# ====================================================================================================
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
        # A promiscuous creation needs its mapping; trunk secondary from the harness trunk member is the known incident.
        ({"pvlan_mode": "promiscuous", "pvlan_association": None}, "pvlan_mapping is required"),
        ({"pvlan_mode": "trunk secondary"}, "Known incident pending engineering"),
        ({"peer2_members": [M2, "e1/8"]}, "duplicate physical"),
        ({"peer1_pcid": 0}, "peer1_pcid must be an integer from 1 to 4096"),  # CHILD-IDS: 11 is valid now (test_pvlan_vpc_identity.py)
        ({"peer1_pcid": None}, "must not be null"),
        ({"pvlan_association": []}, "empty pvlan_association"),
        ({"peer1_cmds": ["no shutdown"]}, "owned by a structured field"),  # RC1: freeform rule
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
        # `overridden` is implemented (test_pvlan_ethernet_lifecycle.py)
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


def _peer2_member_admin_unknown(c):
    # ADMIN-UP-JOIN: an explicit "true" now joins (measured); an administrative state that is not an explicit true/false stays a refusal.
    c.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = ""


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
        (_peer2_member_admin_unknown, "administrative state is unknown"),
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
    ctrl.children_on_save = False  # [UNK]: the first live case measures when the children appear
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
    # A1: the description of ONE peer is now supported (test_pvlan_vpc_description.py); the freeform of one peer is still refused
    for key in ("peer1_cmds", "peer2_cmds"):
        ctrl = created_ctrl()
        converged_previews(ctrl)
        status, result = run_vpc(ctrl, [vpc_item(**{key: ["logging event port link-status"]})], state="merged")
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
    # MM-B: the member case moved to test_pvlan_po_members.py (a member change follows the regular rule now)
    for item, needle in ((promiscuous, "changing pvlan_mode of an existing vPC"),):
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
    # Measured for a regular Po, inferred for a vPC: the controller releases each member ADMIN_STATE "true"; the module sets ONLY
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
    assert verification["state"] == "verified" and verification["parent"] == "not listed"
    assert verification["peers"] == {SN1: "verified", SN2: "verified"}
    assert sorted(ctrl.previews_asked()) == [SN1, SN2] and [g["targets"][VPC] for g in result["pvlan_gate"]] == ["deploy", "deploy"]
    # After the deploy the module reads ONE summary per peer, and nothing else
    assert reads_after_deploy(ctrl) == ["summary %s" % SN1, "summary %s" % SN2]


def reads_after_deploy(ctrl):
    """The GETs sent after the LAST deploy, as "<kind> <serial>" (summary = interface/detail, bulk = interface, policies = policy list)."""
    last = max(i for i, c in enumerate(ctrl.calls) if c[0] == "POST" and c[1].endswith("/rest/globalInterface/deploy"))
    out = []
    for method, path, _data in ctrl.calls[last + 1:]:
        if method != "GET":
            continue
        if "/rest/interface/detail?serialNumber=" in path:
            out.append("summary " + path.split("serialNumber=")[1])
        elif "/control/policies/switches/" in path:
            out.append("policies " + path.rsplit("/", 1)[1])
        elif "/rest/interface?serialNumber=" in path:
            out.append("bulk " + path.split("serialNumber=")[1].split("&")[0])
        else:
            out.append(path)
    return out


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
    c.parents[VPC]["nvPairs"]["PVLAN_MODE"] = "bogus"  # the four submodes are deletable; an unknown one is not


def _pcid_points_to_a_child_that_is_not_there(c):
    # CHILD-IDS: the parent says peer 2's child is port-channel11, the peer holds port-channel10 only: a partial state, never a guess
    c.parents[VPC]["nvPairs"]["PEER2_PCID"] = "11"


def _pcid_unreadable(c):
    c.parents[VPC]["nvPairs"]["PEER2_PCID"] = "bogus"


def _two_members_on_peer1(c):
    c.parents[VPC]["nvPairs"]["PEER1_MEMBER_INTERFACES"] = M1 + ",Ethernet1/9"


def _member2_admin_unknown(c):
    # An up member is released to the fabric default; an unknown administrative state stays refused
    c.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = "maybe"


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
        (_pcid_points_to_a_child_that_is_not_there, "partial state"),
        (_pcid_unreadable, "not a readable port-channel number"),
        (_two_members_on_peer1, "child port-channel or member could not be read"),
        (_member2_admin_unknown, "unknown administrative state"),
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
        # Deploy false now SAVES the deletion (test_pvlan_po_vpc_common.py)
        ({"check_mode": True}, {}, "refused in check mode"),
        # True is a supported default now (released members stay up); an unreadable one refuses
        ({"fabric_admin": "maybe"}, {}, "HOST_INTF_ADMIN_STATE"),
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
    # BOTH members are proved before the first member modify, so peer 2's residue stops the run with NO member write on either
    # peer (the mark-delete stays confirmed: never "zero writes" globally), every member write pending, nothing deployed
    assert "on peer 1 ADMIN_STATE false" not in result["msg"] and "Member writes per serial: %s=pending, %s=pending" % (SN1, SN2) in result["msg"]
    assert ctrl.modifies() == [] and ctrl.deploys() == [] and len(ctrl.markdeletes()) == 1
    assert ctrl.nodes[SN1][M1]["nvPairs"]["ADMIN_STATE"] == "true" and ctrl.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] == "true"
    record = result["pvlan_vpc_release"][-1]
    assert record["peer"] == 2 and record["uncertain_writes"] == [] and len(record["confirmed_writes"]) == 1
    assert record["member_writes"] == {SN1: "pending", SN2: "pending"}


class LateResidue(VpcController):
    """A residue policy owned by the vPC on the second peer only, present before the deploy (`before`) or appearing only AFTER it."""

    def __init__(self, before=False):
        super(LateResidue, self).__init__()
        self.before = before

    def residue(self):
        self.policies_extra[SN2] = [
            dict(entityName="Ethernet1/60", entityType="INTERFACE", templateName="int_eth", source=VPC, deleted=False, policyId="RES", serialNumber=SN2)
        ]

    def __call__(self, mod, method, path, data=None):
        if self.before and method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            self.residue()
        resp = super(LateResidue, self).__call__(mod, method, path, data)
        if not self.before and method == "POST" and path.endswith("/rest/globalInterface/deploy"):
            self.residue()
        return resp


def test_a_residue_policy_on_the_second_peer_only_is_refused_before_the_deploy():
    """The residue that the post-deploy policy read used to catch is judged on the FRESH release proof, before any deploy."""
    ctrl = LateResidue(before=True).seed_baseline().seed_vpc()
    ctrl.next_invocation()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "(peer 2)" in result["msg"] and "live policies still reference the vPC or its child port-channel" in result["msg"]
    assert ctrl.deploys() == [] and len(ctrl.markdeletes()) == 1, "nothing is deployed over a residue"
    assert "pvlan_verification" not in result


def test_a_residue_that_appears_only_after_the_deploy_is_not_read_again_by_the_module():
    """DF-2 contract: after the deploy only the summaries are read; a policy written by another
    party after the pre-deploy proof is outside the module's verification (the external test harness checks the policy list)."""
    ctrl = LateResidue().seed_baseline().seed_vpc()
    ctrl.next_invocation()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified", result.get("msg")
    assert reads_after_deploy(ctrl) == ["summary %s" % SN1, "summary %s" % SN2]
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
        # intermittent, never BOTH peers readable in one round: a summary read makes up to 3 transport attempts, so each peer loses a whole
        # read (3 x 500) in alternate rounds
        {SN1: [True, True, True, False] * 6, SN2: [False, True, True, True] * 6},
    ],
)
def test_unreadable_state_after_the_deletion_is_never_a_verified_deletion(flaky):
    ctrl = created_ctrl()
    delete_previews(ctrl)
    ctrl.summary_failures = flaky  # The summaries are the only post-deploy reads
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "release could not be verified" in result["msg"]
    assert "the interface summary of" in result["msg"] and "could not be read authoritatively" in result["msg"]
    assert result["pvlan_verification"][VPC]["state"] == "failed" and result["pvlan_verification"][VPC]["parent"] == "unreadable"
    release_only(ctrl)
    assert len(ctrl.markdeletes()) == 1


def test_the_policy_list_is_not_read_after_the_deploy():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    ctrl.policy_failures = {SN1: [True] * 40, SN2: [True] * 40}  # would fail every post-deploy policy read (no longer read)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified", result.get("msg")
    assert not any(r.startswith("policies") or r.startswith("bulk") for r in reads_after_deploy(ctrl))


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


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_e4_controls.py
# Controls of the vPC port-channel reconciliation. NOT LIVE TESTED.
#
# Everything vPC-specific here is INFERRED from the MEASURED regular-Po behaviour: the fixtures are simulated.
# Controls: persisted channel-group form (no force outside the pending), the released member kept shut (no shutdown / no write when
# already shut), a repeated deletion, partial peer states, an unknown mark-delete answer, and the Po/vPC target separation.
# ====================================================================================================
def test_the_persisted_member_form_has_no_force_and_the_pending_form_is_the_only_one_that_carries_it():
    persisted = member_after("Ethernet1/7")
    pending = create_pending("Ethernet1/7")
    flat = json.dumps(persisted)
    assert "channel-group 10 mode active" in flat and "force" not in flat
    assert "channel-group 10 force mode active" in json.dumps(pending)


def test_a_member_already_shut_after_the_release_is_not_written_at_all():
    ctrl = created_ctrl()
    ctrl.release_admin_up = False  # the controller already returns the members ADMIN_STATE false
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit", result.get("msg")
    assert ctrl.modifies() == [] and len(ctrl.deploys()) == 1 and len(ctrl.markdeletes()) == 1
    assert all(r.get("member_modify") in (None, "", "not needed") or "ADMIN_STATE" not in r["member_modify"] for r in result.get("pvlan_vpc_release", []))


def test_a_repeated_deletion_after_a_completed_one_writes_nothing():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    assert run_vpc(ctrl, [vpc_del_item()], state="deleted")[0] == "exit"
    before = len(ctrl.writes())
    ctrl.next_invocation()
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is False
    assert len(ctrl.writes()) == before, "a second invocation must not write again"


def test_a_failing_member_modify_on_the_second_peer_stops_before_the_deploy_with_peer_one_confirmed():
    ctrl = created_ctrl()
    ctrl.member_modify_fail = {SN2}
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], result.get("msg")
    assert "peer 2" in result["msg"] and "recovery is a human decision" in result["msg"]
    assert "legacy interface/modify of %s on peer 1 ADMIN_STATE false" % M1 in result["msg"]
    assert ctrl.nodes[SN1][M1]["nvPairs"]["ADMIN_STATE"] == "false"


@pytest.mark.parametrize(
    "answer",
    [
        {"RETURN_CODE": 200, "METHOD": "POST", "MESSAGE": "OK", "DATA": {}},
        {"RETURN_CODE": 200, "METHOD": "POST", "MESSAGE": "OK", "DATA": {"value": []}},
        {"RETURN_CODE": 500, "METHOD": "POST", "MESSAGE": "Internal Server Error", "DATA": "boom"},
    ],
    ids=["no-value-item", "empty-value", "http-500"],
)
def test_an_unknown_markdelete_answer_blocks_the_release_and_the_deploy_and_is_not_retried(answer):
    ctrl = created_ctrl()
    ctrl.markdelete_responses = [answer]
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [] and ctrl.modifies() == []
    assert len(ctrl.markdeletes()) == 1, "one attempt: the answer is not retried"
    assert "UNVERIFIED" in result["msg"] or "UNVERIFIED".lower() in result["msg"].lower()


def test_the_child_port_channel_listed_as_marked_for_deletion_is_accepted_until_the_deploy():
    ctrl = created_ctrl()
    ctrl.children_marked_deleted = True
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit", result.get("msg")
    release_only(ctrl)
    assert len(ctrl.deploys()) == 1


def test_a_vpc_deletion_never_runs_the_regular_port_channel_steps():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit"
    assert len(ctrl.markdeletes()) == 1, "exactly the vPC mark-delete; the Po G4 step does not ALSO fire on the vPC target"
    assert not result.get("pvlan_po_release") and "pvlan_vpc_release" in result
    assert {r["peer"] for r in result["pvlan_vpc_release"]} == {1, 2}


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_e5.py
# Controls of two corrections made after the first live vPC cycle. NOT LIVE TESTED for these corrections.
#
# F1: the created vPC parent carries `createVpc` = "true" (MEASURED): read-only controller metadata, not a template field.
# F2: the child Po of a deleted vPC is listed `interface_delete` whose source is the PARENT vPC (MEASURED).
# The fixtures come from the sanitized captures in fixtures/pvlan_vpc_lifecycle.json; the harness stays SIMULATED elsewhere.
# ====================================================================================================
FX = load_case("pvlan_vpc_l1e4_measured")


def measured_ctrl(**kw):
    """created_ctrl whose parent carries EXACTLY the nvPairs captured live on a created vPC (createVpc included)."""
    ctrl = created_ctrl(**kw)
    ctrl.parents[VPC]["nvPairs"] = copy.deepcopy(FX["created_parent_nvpairs_A1_A2"])
    return ctrl


def test_the_measured_parent_is_what_the_fixture_says_createVpc_is_a_string_true_outside_the_template():
    nv = FX["created_parent_nvpairs_A1_A2"]
    assert nv["createVpc"] == "true" and "createVpc" not in P.VPC_KNOWN_HAVE_NVPAIRS
    assert P.VPC_CONTROLLER_METADATA == {"createVpc": ("true", "false")}


def test_repeat_of_the_measured_parent_writes_nothing_and_still_judges_both_peers():
    ctrl = measured_ctrl()
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == [] and ctrl.deploys() == []
    assert sorted(ctrl.previews_asked()) == [SN1, SN2]


@pytest.mark.parametrize("value", ["maybe", "TRUE ", "1", {"x": 1}], ids=["word", "padded-boolean-is-the-same-metadata", "digit", "object"])
def test_any_other_createVpc_value_stays_unclassifiable_and_blocks_before_a_write(value):
    ctrl = measured_ctrl()
    ctrl.parents[VPC]["nvPairs"]["createVpc"] = value
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    if str(value).strip().lower() in ("true", "false"):
        assert status == "exit" and ctrl.writes() == []  # a padded exact boolean is the same metadata
    else:
        assert status == "fail" and "createVpc" in result["msg"] and "cannot classify" in result["msg"], result.get("msg")
        assert ctrl.writes() == [] and ctrl.deploys() == []


def test_an_unknown_second_nvpair_next_to_createVpc_still_blocks_naming_only_that_one():
    ctrl = measured_ctrl()
    ctrl.parents[VPC]["nvPairs"]["someNewKey"] = "x"
    converged_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and "someNewKey" in result["msg"] and "createVpc" not in result["msg"].split("classify")[-1], result.get("msg")
    assert ctrl.writes() == []


def _updated(ctrl, previews, item, state):
    for serial, port in ((SN1, M1), (SN2, M2)):
        ctrl.vpc_previews[serial] = [previews[0](serial, port), previews[1](serial, port)]
    status, result = run_vpc(ctrl, [item], state=state)
    assert status == "exit" and len(ctrl.modifies()) == 1, result.get("msg")
    return json.loads(ctrl.modifies()[0][2])[0]["interfaces"][0]["nvPairs"]


def test_a_merged_update_of_the_measured_parent_echoes_createVpc_unchanged_never_dropped():
    from .helpers.vpc_controller import converged_preview, pc_mode_preview

    sent = _updated(measured_ctrl(), (converged_preview, pc_mode_preview), vpc_item(pc_mode="passive"), "merged")
    assert sent["createVpc"] == "true" and sent["PC_MODE"] == "passive", "the controller's own metadata value travels back unchanged"


def test_a_replaced_update_of_the_measured_parent_echoes_createVpc_unchanged_never_dropped():
    from .helpers.vpc_controller import PRIMARY, SECONDARY, converged_preview, update_preview

    new = 2213
    item = vpc_item(pvlan_association=[{"primary_vlan": PRIMARY, "secondary_vlan": new}])
    sent = _updated(measured_ctrl(), (converged_preview, lambda s, p: update_preview(s, p, (PRIMARY, SECONDARY), (PRIMARY, new))), item, "replaced")
    assert sent["createVpc"] == "true"


def test_creation_never_writes_createVpc_the_controller_adds_it():
    from .helpers.vpc_controller import baseline_ctrl, create_previews

    ctrl = baseline_ctrl()
    create_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit", result.get("msg")
    body = json.loads(ctrl.creates()[0][2])
    assert "createVpc" not in json.dumps(body)


def test_the_marked_child_of_the_measured_form_is_accepted_only_for_its_own_vpc():
    entry = dict(copy.deepcopy(FX["child_marked_for_deletion_F"]), serialNo=SN1)  # the sanitized MEASURED entry of peer 1 (markDeleted true)
    entry["ifName"] = "port-channel10"
    entry["underlayPolicies"][0]["serialNumber"] = SN1
    assert FX["child_marked_for_deletion_F"]["underlayPolicies"][0]["source"] == "vpc10"
    assert P.po_marked_deleted_problem(entry, "port-channel10", parent="vPC10") is None
    assert "owned by 'vpc11'" in P.po_marked_deleted_problem(entry, "port-channel10", parent="vpc11")
    # a regular Po keeps its own ownership rule: source == the port-channel
    assert "owned by 'port-channel10'" in P.po_marked_deleted_problem(entry, "port-channel10")
    regular = copy.deepcopy(entry)
    regular["underlayPolicies"][0]["source"] = "port-channel10"  # the measured regular-Po form
    assert P.po_marked_deleted_problem(regular, "port-channel10") is None
    assert P.po_marked_deleted_problem(regular, "port-channel10", parent="vpc10") is not None, "a vPC child owned by its Po name is refused"
    other = copy.deepcopy(entry)
    other["underlayPolicies"][0]["templateName"] = "int_vpc_pvlan_po"
    assert P.po_marked_deleted_problem(other, "port-channel10", parent="vpc10") is not None


def test_full_deletion_with_the_measured_parent_source_writes_both_members_down_before_the_single_deploy():
    ctrl = measured_ctrl()
    ctrl.children_marked_deleted = True  # MEASURED: marked for deletion, source = the parent vPC
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.deploys()) == 1
    bodies = release_only(ctrl)  # two legacy modifies, ADMIN_STATE false, all before the deploy
    assert sorted(b[0]["interfaces"][0]["serialNumber"] for b in bodies) == [SN1, SN2]
    assert result["pvlan_verification"][VPC]["state"] == "verified"
    assert [r["peer"] for r in result["pvlan_vpc_release"]] == [1, 2]


@pytest.mark.parametrize("source", ["vpc11", "port-channel10", "vPC1", ""], ids=["other-vpc", "the-po-itself", "prefix", "empty"])
def test_a_marked_child_owned_by_another_parent_is_refused_before_any_member_write_or_deploy(source):
    ctrl = measured_ctrl()
    ctrl.children_marked_deleted = True
    ctrl.marked_source = source
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "member release failed while proving the released member" in result["msg"], result.get("msg")
    assert "still listed" in result["msg"] and ctrl.modifies() == [] and ctrl.deploys() == []
    assert len(ctrl.markdeletes()) == 1, "the one mark-delete is reported as confirmed; nothing else was written"


def test_an_uncertain_member_modify_after_the_measured_form_still_stops_before_the_deploy():
    ctrl = measured_ctrl()
    ctrl.children_marked_deleted = True
    ctrl.member_modify_fail = {SN2}
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.deploys() == [] and "peer 2" in result["msg"], result.get("msg")
    assert "ADMIN_STATE false" in result["msg"]


def test_the_vpc_child_model_carries_the_template_default_bpduguard_enable_measured_on_the_live_po():
    nv = FX["created_parent_nvpairs_A1_A2"]
    assert nv["BPDUGUARD_ENABLED"] == "true", "measured parent default; the child Po therefore renders `spanning-tree bpduguard enable`"
    from .helpers.vpc_controller import po_stanza

    assert "  spanning-tree bpduguard enable" in po_stanza()
