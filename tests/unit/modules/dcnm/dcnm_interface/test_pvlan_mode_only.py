"""Host-mode PVLAN port-channel and vPC prepared without a direct association, for network attachments.

NOT LIVE TESTED. Real main(); only the controller boundary is intercepted, through the existing harnesses
(helpers/port_channel_controller, helpers/vpc_controller).

Inputs:
  * MEASURED (legacy REST, NDFC 12.6.0.267): a host port-channel and a host vPC created with ASSOCIATION_LIST and
    MAPPING_LIST both '' are accepted and stored with both lists ''; the GUI then attaches a PVLAN network to them.
  * MEASURED (policy list, same controller): a network attachment adds ONE policy to the attached port-channel (on a vPC,
    to the child port-channel of each attached peer): templateName NA, source OVERLAY, entityType Interface, priority 1525,
    secondaryEntityType Config_Profile, secondaryEntityName the network, generatedConfig the interface header plus
    `switchport private-vlan host-association P S`. The interface summary keeps listing only the direct policy and the
    members get no OVERLAY policy. After a saved port detach the OVERLAY policy stays listed with deleted true and
    priority -1525 until the network deploy (measured on an Ethernet port; assumed for a port-channel).
  * SYNTHETIC: every preview of a mode-only aggregate (the measured host stanzas without the association line) and the
    In-Sync attached state; no attached port-channel or vPC was deployed and read back.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .helpers import vpc_controller as V
from .helpers.ethernet_controller import IF7, SERIAL, run, trunk_host_nv
from .helpers.port_channel_controller import (
    PO,
    PO_HOST,
    PO_MEMBER,
    PoLifecycleController,
    baseline,
    create_preview,
    del_item,
    delete_preview,
    item,
)

ASSOC = [{"primary_vlan": 2210, "secondary_vlan": 2212}]
MODIFY = "/rest/interface/modify"


def overlay(entity, network="PV_ISOLATED", pair=(2210, 2212), **over):
    """The MEASURED shape of the policy a network attachment adds to a host port-channel."""
    policy = {
        "policyId": "PROFILE-NETWORK-27",
        "entityType": "Interface",
        "entityName": entity,
        "templateName": "NA",
        "priority": 1525,
        "source": "OVERLAY",
        "deleted": False,
        "secondaryEntityName": network,
        "secondaryEntityType": "Config_Profile",
        "serialNumber": None,
        "generatedConfig": "interface %s\n  switchport private-vlan host-association %d %d\n" % (entity, pair[0], pair[1]),
    }
    policy.update(over)
    return policy


def detached(entity, **over):
    """The MEASURED listing of an OVERLAY policy whose port detach is saved but not deployed."""
    return overlay(entity, deleted=True, priority=-1525, **over)


def writes(ctrl):
    return [c for c in ctrl.calls if c[0] in ("POST", "PUT", "DELETE") and "/config-preview/" not in c[1]]


def without_list(lines):
    return [line for line in lines if "host-association" not in line]


# ====================================================================================================================
# Regular port-channel
# ====================================================================================================================
def mode_only_po_ctrl(members=(IF7,)):
    """An existing host port-channel stored with both lists '' (as the measured REST creation stores it) and its member."""
    ctrl = PoLifecycleController()
    nv = P.po_host_nvpairs({"pvlan_mode": "host", "members": list(members), "admin_state": False}, PO)
    ctrl.detail[PO] = {"policy": PO_HOST, "nvPairs": nv}
    ctrl.po_names.add(PO)
    for member in members:
        ctrl.detail[member] = {
            "policy": PO_MEMBER,
            "nvPairs": {
                "PO_ID": PO, "PC_MODE": "active", "PVLAN_MODE": "host", "CDP_ENABLE": "true", "lldpTransmit": "false",
                "lldpReceive": "false", "LACP_PORT_PRIO": "32768", "LACP_RATE": "normal", "DESC": "", "CONF": "",
                "ADMIN_STATE": "false", "INTF_NAME": member,
            },
        }
    ctrl.next_invocation()
    return ctrl


def attached_po_ctrl(**over):
    ctrl = mode_only_po_ctrl()
    ctrl.policies_extra = [overlay("Port-channel10", **over)]
    return ctrl


def po_create_body(ctrl):
    body = json.loads(ctrl.creates()[0][2])
    return body[0] if isinstance(body, list) else body


@pytest.mark.parametrize("association", ["omitted", "empty"])
def test_po_host_creation_without_association_sends_the_neutral_lists(association):
    ctrl = baseline()
    ctrl.previews = [create_preview("host", [])]
    profile = {} if association == "omitted" else {"pvlan_association": []}
    status, result = run(ctrl, [item("host", **profile)], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    payload = po_create_body(ctrl)
    nv = payload["interfaces"][0]["nvPairs"]
    assert payload["policy"] == PO_HOST and payload["interfaces"][0]["ifName"] == PO
    assert (nv["PVLAN_MODE"], nv["ASSOCIATION_LIST"], nv["MAPPING_LIST"], nv["MEMBER_INTERFACES"]) == ("host", "", "", IF7)
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    assert ctrl.requests("POST", MODIFY) == [], "the member is written by the parent's template, never by the module"
    assert ctrl.detail[PO]["nvPairs"]["ASSOCIATION_LIST"] == ""


@pytest.mark.parametrize("profile", [{}, {"pvlan_association": ASSOC}])
def test_po_creation_in_check_mode_is_refused_with_or_without_association(profile):
    """Unchanged contract: the pre-deploy gate needs the saved intent, so no PVLAN creation is shown in check mode."""
    ctrl = baseline()
    status, result = run(ctrl, [item("host", **profile)], check_mode=True)
    assert status == "fail" and "creating a PVLAN port-channel is refused in check mode" in result["msg"], result.get("msg")
    assert writes(ctrl) == []


@pytest.mark.parametrize("mode, needle", [
    ("promiscuous", "pvlan_mapping is required to create a port-channel in pvlan_mode promiscuous"),
    ("trunk promiscuous", "pvlan_mapping is required to create a port-channel in pvlan_mode trunk promiscuous"),
    ("trunk secondary", "pvlan_association is required to create a port-channel in pvlan_mode trunk secondary"),
])
def test_po_creation_without_a_list_stays_refused_outside_host_mode(mode, needle):
    ctrl = baseline(mode)
    status, result = run(ctrl, [item(mode)])
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert writes(ctrl) == []


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
@pytest.mark.parametrize("association", ["omitted", "empty"])
def test_po_mode_only_repeat_is_quiet(state, association):
    ctrl = mode_only_po_ctrl()
    profile = {} if association == "omitted" else {"pvlan_association": []}
    status, result = run(ctrl, [item("host", **profile)], state=state)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == []


def test_po_mode_only_repeat_after_creation_through_the_module_is_quiet():
    ctrl = baseline()
    ctrl.previews = [create_preview("host", [])]
    status, result = run(ctrl, [item("host")])
    assert status == "exit", result.get("msg")
    ctrl.detail[IF7] = mode_only_po_ctrl().detail[IF7]
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [item("host")])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == []


def test_po_mode_only_query_reports_the_empty_lists_without_writes():
    ctrl = mode_only_po_ctrl()
    status, result = run(ctrl, [{"name": "po10", "type": "pc", "switch": ["10.0.0.1"]}], state="query")
    assert status == "exit", result.get("msg")
    assert writes(ctrl) == []
    found = [i for r in result["response"] for i in (r.get("interfaces") or []) if i.get("ifName") == PO]
    assert found and (found[0]["nvPairs"]["ASSOCIATION_LIST"], found[0]["nvPairs"]["MAPPING_LIST"]) == ("", "")


def test_po_mode_only_deletion_releases_the_member_and_repeats_quietly():
    ctrl = mode_only_po_ctrl()
    ctrl.previews = [delete_preview("host", [])]
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.deploys()) == 1
    assert PO not in ctrl.detail and ctrl.detail[IF7]["policy"] == "int_trunk_host"
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == []


# ---------------------------------------------------------------- port-channel attached to a network
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
@pytest.mark.parametrize("deploy", [True, False])
def test_po_attached_unchanged_repeat_is_a_verified_noop(state, deploy):
    ctrl = attached_po_ctrl()
    before = (json.dumps(ctrl.detail, sort_keys=True), json.dumps(ctrl.policies_extra, sort_keys=True))
    status, result = run(ctrl, [item("host", deploy=deploy)], state=state)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == [] and ctrl.requests(mark="/config-preview/") == []
    assert (json.dumps(ctrl.detail, sort_keys=True), json.dumps(ctrl.policies_extra, sort_keys=True)) == before
    owned = result["pvlan_network_owned"]
    assert owned == [{"interface": PO, "serial": SERIAL, "networks": ["PV_ISOLATED"],
                      "state": "unchanged; the association belongs to the network attachment (nothing written)"}]


def test_po_attached_unchanged_repeat_in_check_mode_is_a_noop():
    ctrl = attached_po_ctrl()
    status, result = run(ctrl, [item("host")], check_mode=True)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == []


@pytest.mark.parametrize("profile", [
    {"description": "edited"},
    {"admin_state": True},
    {"pvlan_association": ASSOC},
    {"members": [IF7, "Ethernet1/8"]},
    {"pc_mode": "passive"},
])
def test_po_attached_edit_is_refused_before_any_write(profile):
    ctrl = attached_po_ctrl()
    ctrl.detail["Ethernet1/8"] = {"policy": "int_trunk_host", "nvPairs": trunk_host_nv("Ethernet1/8")}
    status, result = run(ctrl, [item("host", **profile)])
    assert status == "fail" and "network attachment" in result["msg"] and "PV_ISOLATED" in result["msg"], result.get("msg")
    assert writes(ctrl) == []


@pytest.mark.parametrize("deploy", [True, False])
def test_po_attached_deletion_is_refused_before_any_write(deploy):
    ctrl = attached_po_ctrl()
    status, result = run(ctrl, [dict(del_item(), deploy=deploy)], state="deleted")
    assert status == "fail" and writes(ctrl) == [], result.get("msg")


@pytest.mark.parametrize("deploy", [True, False])
@pytest.mark.parametrize("where", [PO, IF7])
def test_po_attached_out_of_sync_is_reported_not_converged(deploy, where):
    ctrl = attached_po_ctrl()
    ctrl.summary[where] = {"complianceStatus": "Out-of-Sync"}
    status, result = run(ctrl, [item("host", deploy=deploy)])
    assert status == "fail" and "Out-of-Sync" in result["msg"] and "PV_ISOLATED" in result["msg"], result.get("msg")
    assert writes(ctrl) == []


def unknown_owner(kind, entity):
    """One deviation from the measured OVERLAY shape of `entity`."""
    association = "  switchport private-vlan host-association 2210 2212\n"
    return {
        "other template": dict(templateName="int_port_channel_trunk_host"),
        "other secondary entity type": dict(secondaryEntityType="Interface"),
        "no network name": dict(secondaryEntityName=""),
        "other priority": dict(priority=500),
        "other entity type": dict(entityType="SWITCH"),
        "mapping line": dict(generatedConfig="interface %s\n  switchport private-vlan mapping 2210 2212\n" % entity),
        "extra line": dict(generatedConfig="interface %s\n%s  shutdown\n" % (entity, association)),
        "other interface": dict(generatedConfig="interface Port-channel99\n" + association),
        "no generated config": dict(generatedConfig=None),
        "lower-case source": dict(source="overlay"),
    }[kind]


UNKNOWN_OWNERS = ("other template", "other secondary entity type", "no network name", "other priority", "other entity type",
                  "mapping line", "extra line", "other interface", "no generated config", "lower-case source")


@pytest.mark.parametrize("kind", UNKNOWN_OWNERS)
def test_po_unrecognized_overlay_owner_is_refused(kind):
    ctrl = attached_po_ctrl(**unknown_owner(kind, "Port-channel10"))
    status, result = run(ctrl, [item("host")])
    assert status == "fail" and writes(ctrl) == [], (kind, result.get("msg"))


def test_po_two_overlay_owners_are_refused():
    ctrl = attached_po_ctrl()
    ctrl.policies_extra.append(overlay("Port-channel10", network="PV_OTHER", policyId="PROFILE-NETWORK-28"))
    status, result = run(ctrl, [item("host")])
    assert status == "fail" and writes(ctrl) == [], result.get("msg")


def test_po_overlay_on_the_member_is_refused():
    ctrl = mode_only_po_ctrl()
    ctrl.policies_extra = [overlay("Port-channel10"), overlay(IF7, policyId="PROFILE-NETWORK-29")]
    status, result = run(ctrl, [item("host")])
    assert status == "fail" and writes(ctrl) == [], result.get("msg")


@pytest.mark.parametrize("member_nv", [{"PO_ID": "Port-channel11"}, {"PO_ID": ""}])
def test_po_attached_with_a_member_of_another_port_channel_is_refused(member_nv):
    ctrl = attached_po_ctrl()
    ctrl.detail[IF7]["nvPairs"].update(member_nv)
    status, result = run(ctrl, [item("host")])
    assert status == "fail" and IF7 in result["msg"] and writes(ctrl) == [], result.get("msg")


def test_po_attached_with_an_extra_policy_on_the_member_is_refused():
    ctrl = attached_po_ctrl()
    ctrl.policies_extra.append({"entityName": IF7, "entityType": "INTERFACE", "templateName": "int_freeform", "source": "", "deleted": False,
                                "policyId": "POLICY-990", "priority": 500, "serialNumber": SERIAL})
    status, result = run(ctrl, [item("host")])
    assert status == "fail" and "int_freeform" in result["msg"] and writes(ctrl) == [], result.get("msg")


@pytest.mark.parametrize("value", ["not-a-list", '{"ASSOCIATION_LIST":[{"P_VLAN":"x"}]}'])
def test_po_attached_with_a_malformed_direct_list_is_refused(value):
    ctrl = attached_po_ctrl()
    ctrl.detail[PO]["nvPairs"]["ASSOCIATION_LIST"] = value
    status, result = run(ctrl, [item("host")])
    assert status == "fail" and writes(ctrl) == [], result.get("msg")


def test_po_attached_with_a_direct_association_is_refused():
    ctrl = attached_po_ctrl()
    ctrl.detail[PO]["nvPairs"]["ASSOCIATION_LIST"] = P.pairs_to_wire("ASSOCIATION_LIST", [(2210, 2212)])
    status, result = run(ctrl, [item("host", pvlan_association=ASSOC)])
    assert status == "fail" and writes(ctrl) == [], result.get("msg")


@pytest.mark.parametrize("key", ["ASSOCIATION_LIST", "MAPPING_LIST"])
def test_po_attached_with_a_missing_list_key_is_refused(key):
    ctrl = attached_po_ctrl()
    ctrl.detail[PO]["nvPairs"].pop(key)
    status, result = run(ctrl, [item("host")])
    assert status == "fail" and writes(ctrl) == [], result.get("msg")


@pytest.mark.parametrize("request_item, state", [("repeat", "merged"), ("delete", "deleted")])
def test_po_saved_network_detach_is_a_pending_removal_not_a_converged_state(request_item, state):
    ctrl = mode_only_po_ctrl()
    ctrl.policies_extra = [detached("Port-channel10")]
    config = [item("host")] if request_item == "repeat" else [del_item()]
    status, result = run(ctrl, config, state=state)
    assert status == "fail" and "not deployed" in result["msg"], result.get("msg")
    assert writes(ctrl) == []


def test_po_after_the_deployed_network_detach_is_deleted_normally():
    ctrl = attached_po_ctrl()
    ctrl.policies_extra = []  # the network deploy purged the OVERLAY policy (measured on an Ethernet port)
    ctrl.previews = [delete_preview("host", [])]
    status, result = run(ctrl, [del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and ctrl.detail[IF7]["policy"] == "int_trunk_host"


# ---------------------------------------------------------------- existing direct association (controls)
def direct_po_ctrl():
    ctrl = mode_only_po_ctrl()
    ctrl.detail[PO]["nvPairs"]["ASSOCIATION_LIST"] = P.pairs_to_wire("ASSOCIATION_LIST", [(2210, 2212)])
    return ctrl


@pytest.mark.parametrize("association", ["omitted", "empty"])
def test_po_merged_without_a_list_keeps_an_existing_direct_association(association):
    ctrl = direct_po_ctrl()
    profile = {} if association == "omitted" else {"pvlan_association": []}
    status, result = run(ctrl, [item("host", deploy=False, **profile)])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert writes(ctrl) == []


def test_po_replaced_without_a_list_still_clears_an_existing_direct_association():
    ctrl = direct_po_ctrl()
    status, result = run(ctrl, [item("host", deploy=False)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    policy, nv = ctrl.sent_nv(PO)
    assert policy == PO_HOST and nv["ASSOCIATION_LIST"] == "" and nv["MAPPING_LIST"] == ""


# ====================================================================================================================
# vPC
# ====================================================================================================================
def vpc_mode_only_item(association="omitted", pcids=(10, 10), **profile):
    out = V.vpc_item(peer1_pcid=pcids[0], peer2_pcid=pcids[1], **profile)
    if association == "omitted":
        out["profile"].pop("pvlan_association")
    elif association == "empty":
        out["profile"]["pvlan_association"] = []
    return out


def vpc_mode_only_previews(ctrl, kind, pcids=("10", "10")):
    builders = {"create": V.create_preview, "converged": V.converged_preview}
    for serial, port in V.PEERS:
        answer = builders[kind](serial, port)
        for entry in answer["DATA"]:
            for key in ("pendingConfig", "runningConfig", "expectedConfig"):
                if isinstance(entry.get(key), list):
                    entry[key] = without_list(entry[key])
        ctrl.vpc_previews[serial] = [answer]
    return V.remap(ctrl, pcids)


def mode_only_vpc_ctrl(pcids=("10", "11")):
    """An existing host vPC stored with both lists '' (as the measured REST creation stores it), children and members on both peers."""
    ctrl = V.MeasuredVpc().seed_baseline().seed_vpc(association=(), pcids=pcids)
    parent = ctrl.parents[V.VPC]["nvPairs"]
    parent["ASSOCIATION_LIST"] = ""
    ctrl._expand_children(parent)
    ctrl.next_invocation()
    return ctrl


def child(index, pcids=("10", "11")):
    return "port-channel" + pcids[index]


def attached_vpc_ctrl(pcids=("10", "11"), peers=(0, 1), **over):
    ctrl = mode_only_vpc_ctrl(pcids)
    for index in peers:
        serial = (V.SN1, V.SN2)[index]
        ctrl.policies_extra[serial] = [overlay("P" + child(index, pcids)[1:], policyId="PROFILE-NETWORK-%d" % (28 + index), **over)]
    return ctrl


@pytest.mark.parametrize("association", ["omitted", "empty"])
def test_vpc_host_creation_without_association_sends_the_neutral_lists(association):
    ctrl = V.baseline_ctrl()
    vpc_mode_only_previews(ctrl, "create")
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(association)])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    nv = V.sent_nv(ctrl)
    assert (nv["PVLAN_MODE"], nv["ASSOCIATION_LIST"], nv["MAPPING_LIST"]) == ("host", "", "")
    assert (nv["PEER1_MEMBER_INTERFACES"], nv["PEER2_MEMBER_INTERFACES"]) == (V.M1, V.M2)
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1 and ctrl.modifies() == []
    assert sorted(ctrl.previews_asked()) == [V.SN1, V.SN2]
    for serial in (V.SN1, V.SN2):
        assert ctrl.nodes[serial]["port-channel10"]["nvPairs"]["ASSOCIATION_LIST"] == ""


def test_vpc_host_creation_with_unequal_port_channel_numbers():
    ctrl = V.baseline_ctrl()
    vpc_mode_only_previews(ctrl, "create", pcids=("10", "11"))
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    nv = V.sent_nv(ctrl)
    assert (nv["PEER1_PCID"], nv["PEER2_PCID"], nv["ASSOCIATION_LIST"]) == ("10", "11", "")
    assert "port-channel10" in ctrl.nodes[V.SN1] and "port-channel11" in ctrl.nodes[V.SN2]


@pytest.mark.parametrize("association", ["omitted", "nonempty"])
def test_vpc_creation_in_check_mode_is_refused_with_or_without_association(association):
    """Unchanged contract: the pre-deploy gate needs the saved intent, so no PVLAN creation is shown in check mode."""
    ctrl = V.baseline_ctrl()
    entry = vpc_mode_only_item() if association == "omitted" else V.vpc_item()
    status, result = V.run_vpc(ctrl, [entry], check_mode=True)
    assert status == "fail" and "creating a PVLAN vPC is refused in check mode" in result["msg"], result.get("msg")
    assert ctrl.writes() == []


@pytest.mark.parametrize("mode, field", [
    ("promiscuous", "pvlan_mapping"), ("trunk promiscuous", "pvlan_mapping"), ("trunk secondary", "pvlan_association"),
])
@pytest.mark.parametrize("value", ["omitted", "empty"])
def test_vpc_creation_without_a_list_stays_refused_outside_host_mode(mode, field, value):
    ctrl = V.baseline_ctrl()
    entry = vpc_mode_only_item(pvlan_mode=mode)
    if value == "empty":
        entry["profile"][field] = []
    status, result = V.run_vpc(ctrl, [entry])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
@pytest.mark.parametrize("association", ["omitted", "empty"])
def test_vpc_mode_only_repeat_without_deploy_is_quiet(state, association):
    ctrl = mode_only_vpc_ctrl()
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(association, pcids=(10, 11), deploy=False)], state=state)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_vpc_mode_only_repeat_with_deploy_judges_both_peers_and_writes_nothing(state):
    ctrl = mode_only_vpc_ctrl()
    vpc_mode_only_previews(ctrl, "converged", pcids=("10", "11"))
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))], state=state)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == [] and sorted(ctrl.previews_asked()) == [V.SN1, V.SN2]


def test_vpc_mode_only_query_reports_the_empty_lists_without_writes():
    ctrl = mode_only_vpc_ctrl()
    status, result = V.run_vpc(ctrl, [{"name": "vpc10", "type": "vpc", "switch": [V.IP1, V.IP2]}], state="query")
    assert status == "exit", result.get("msg")
    assert ctrl.writes() == []


def test_vpc_mode_only_deletion_releases_both_members():
    ctrl = mode_only_vpc_ctrl(pcids=("10", "10"))
    for serial, port in V.PEERS:
        answer = V.delete_preview(serial, port)
        answer["DATA"][0]["pendingConfig"] = [l for l in answer["DATA"][0]["pendingConfig"] if "host-association" not in l]
        answer["DATA"][0]["runningConfig"] = without_list(answer["DATA"][0]["runningConfig"])
        ctrl.vpc_previews[serial] = [answer]
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and V.VPC not in ctrl.parents
    assert all(ctrl.nodes[serial][port]["policy"] == "int_trunk_host" for serial, port in V.PEERS)


# ---------------------------------------------------------------- existing direct association (controls)
def test_vpc_merged_with_an_empty_list_keeps_an_existing_direct_association():
    ctrl = V.created_ctrl()
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item("empty", deploy=False)])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


@pytest.mark.parametrize("association", ["omitted", "empty"])
def test_vpc_replaced_does_not_clear_an_existing_direct_association(association):
    ctrl = V.created_ctrl()
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(association, deploy=False)], state="replaced")
    assert status == "fail" and "an empty association is not implemented for a vPC" in result["msg"], result.get("msg")
    assert ctrl.writes() == []


# ---------------------------------------------------------------- vPC attached to a network
@pytest.mark.parametrize("state", ["merged", "replaced", "overridden"])
@pytest.mark.parametrize("deploy", [True, False])
def test_vpc_attached_unchanged_repeat_is_a_verified_noop(state, deploy):
    ctrl = attached_vpc_ctrl()
    before = json.dumps([ctrl.parents, ctrl.nodes, ctrl.policies_extra], sort_keys=True)
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11), deploy=deploy)], state=state)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == [] and ctrl.previews_asked() == []
    assert json.dumps([ctrl.parents, ctrl.nodes, ctrl.policies_extra], sort_keys=True) == before
    owned = sorted((o["interface"], o["serial"], tuple(o["networks"])) for o in result["pvlan_network_owned"])
    assert owned == [("port-channel10", V.SN1, ("PV_ISOLATED",)), ("port-channel11", V.SN2, ("PV_ISOLATED",))]


def test_vpc_attached_unchanged_repeat_in_check_mode_is_a_noop():
    ctrl = attached_vpc_ctrl()
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))], check_mode=True)
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


def test_vpc_attached_on_one_peer_only_is_a_noop_for_that_peer():
    ctrl = attached_vpc_ctrl(peers=(1,))
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == [] and ctrl.previews_asked() == []
    assert [(o["interface"], o["serial"]) for o in result["pvlan_network_owned"]] == [("port-channel11", V.SN2)]


@pytest.mark.parametrize("profile", [
    {"peer1_description": "edited"},
    {"admin_state": True},
    {"pvlan_association": ASSOC},
    {"pc_mode": "passive"},
])
def test_vpc_attached_edit_is_refused_before_any_write(profile):
    ctrl = attached_vpc_ctrl()
    entry = vpc_mode_only_item(pcids=(10, 11))
    entry["profile"].update(profile)
    status, result = V.run_vpc(ctrl, [entry])
    assert status == "fail" and "network attachment" in result["msg"] and "PV_ISOLATED" in result["msg"], result.get("msg")
    assert ctrl.writes() == []


def test_vpc_attached_deletion_is_refused_before_any_write():
    ctrl = attached_vpc_ctrl()
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("deploy", [True, False])
@pytest.mark.parametrize("where", ["child", "member"])
def test_vpc_attached_out_of_sync_on_one_peer_is_reported_not_converged(deploy, where):
    ctrl = attached_vpc_ctrl()
    name = child(1) if where == "child" else V.M2
    ctrl.compliance_by[(V.SN2, name)] = "Out-of-Sync"
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11), deploy=deploy)])
    assert status == "fail" and "Out-of-Sync" in result["msg"], result.get("msg")
    assert ctrl.writes() == []


@pytest.mark.parametrize("kind", UNKNOWN_OWNERS)
def test_vpc_unrecognized_overlay_owner_is_refused(kind):
    ctrl = attached_vpc_ctrl(peers=(1,), **unknown_owner(kind, "Port-channel11"))
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))])
    assert status == "fail" and ctrl.writes() == [], (kind, result.get("msg"))


@pytest.mark.parametrize("entity", ["member", "parent"])
def test_vpc_overlay_on_a_member_or_on_the_parent_is_refused(entity):
    ctrl = attached_vpc_ctrl()
    name = V.M2 if entity == "member" else V.VPC
    ctrl.policies_extra[V.SN2].append(overlay(name, policyId="PROFILE-NETWORK-40"))
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


def test_vpc_attached_with_a_direct_association_is_refused():
    ctrl = attached_vpc_ctrl()
    wire = P.pairs_to_wire("ASSOCIATION_LIST", [(2210, 2212)])
    ctrl.parents[V.VPC]["nvPairs"]["ASSOCIATION_LIST"] = wire
    ctrl._expand_children(ctrl.parents[V.VPC]["nvPairs"])
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11), pvlan_association=ASSOC)])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("key", ["ASSOCIATION_LIST", "MAPPING_LIST"])
def test_vpc_attached_with_a_missing_list_key_is_refused(key):
    ctrl = attached_vpc_ctrl()
    ctrl.parents[V.VPC]["nvPairs"].pop(key)
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("value", ["not-a-list", '{"ASSOCIATION_LIST":[{"P_VLAN":"x"}]}'])
def test_vpc_attached_with_a_malformed_direct_list_is_refused(value):
    ctrl = attached_vpc_ctrl()
    ctrl.parents[V.VPC]["nvPairs"]["ASSOCIATION_LIST"] = value
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


def test_vpc_attached_with_a_member_of_another_port_channel_is_refused():
    ctrl = attached_vpc_ctrl()
    ctrl.nodes[V.SN2][V.M2]["nvPairs"]["PO_ID"] = "port-channel99"
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


def test_vpc_attached_with_a_missing_child_on_one_peer_is_refused():
    ctrl = attached_vpc_ctrl()
    ctrl.nodes[V.SN2].pop(child(1))
    status, result = V.run_vpc(ctrl, [vpc_mode_only_item(pcids=(10, 11))])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


@pytest.mark.parametrize("request_item, state", [("repeat", "merged"), ("delete", "deleted")])
def test_vpc_saved_network_detach_is_a_pending_removal_not_a_converged_state(request_item, state):
    ctrl = mode_only_vpc_ctrl()
    ctrl.policies_extra[V.SN2] = [detached("Port-channel11")]
    config = [vpc_mode_only_item(pcids=(10, 11))] if request_item == "repeat" else [V.vpc_del_item()]
    status, result = V.run_vpc(ctrl, config, state=state)
    assert status == "fail" and "not deployed" in result["msg"], result.get("msg")
    assert ctrl.writes() == []


def test_vpc_after_the_deployed_network_detach_is_deleted_normally_on_both_peers():
    ctrl = attached_vpc_ctrl(pcids=("10", "10"))
    ctrl.policies_extra = {V.SN1: [], V.SN2: []}
    for serial, port in V.PEERS:
        answer = V.delete_preview(serial, port)
        answer["DATA"][0]["pendingConfig"] = [l for l in answer["DATA"][0]["pendingConfig"] if "host-association" not in l]
        answer["DATA"][0]["runningConfig"] = without_list(answer["DATA"][0]["runningConfig"])
        ctrl.vpc_previews[serial] = [answer]
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert V.VPC not in ctrl.parents and all(ctrl.nodes[s][p]["policy"] == "int_trunk_host" for s, p in V.PEERS)
