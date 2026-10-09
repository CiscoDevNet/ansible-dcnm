"""PO-HOST-E2-CONFLICTS: membership conflicts INSIDE one invocation (review PO-HOST-E1-R1, finding P1).

NOT LIVE TESTED. Real main(); only the external boundary is mocked, through the E1 test module (which reuses the
existing Ethernet harness). Writes are those INTERCEPTED by the harness, not proof that NDFC accepts or rejects anything.

Success of a rejection = zero configuration writes AND zero deploys. Two families, both config orders, merged and replaced:
  A. a new PVLAN port-channel claims a member that the same invocation also manages directly as an interface;
  B. a new PVLAN port-channel claims a member that another port-channel (non-PVLAN too) claims in the same invocation.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .test_dcnm_intf_pvlan_harness import IF7, IF8, SWITCH_IP, TRUNK, trunk_host_nv, run
from .test_dcnm_intf_pvlan_po_host import _eth, baseline_ctrl, created_ctrl, good_preview, po_item

IF9 = "Ethernet1/9"
ORDERS = ("parent_first", "member_first")
STATES = ("merged", "replaced")


def ordered(order, parent, other):
    return [parent, other] if order == "parent_first" else [other, parent]


def direct_child(name=IF7, **extra):
    item = _eth(name)
    item["profile"]["description"] = "conflicting direct child"
    item["profile"].update(extra)
    return item


def trunk_po(name="po11", members=(IF7,), deploy=False):
    return {"name": name, "type": "pc", "switch": [SWITCH_IP], "deploy": deploy,
            "profile": {"mode": "trunk", "members": list(members), "allowed_vlans": "none"}}


def assert_refused(ctrl, status, result, needle):
    assert status == "fail", result
    assert needle in result["msg"], result["msg"]
    assert ctrl.writes() == [], "a refused invocation must write no configuration"
    assert ctrl.deploys() == [] and ctrl.creates() == []


# ------------------------------------------------------------------ family A: the member is also a direct entry
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("order", ORDERS)
@pytest.mark.parametrize("deploy", [False, True])
def test_member_also_managed_directly_is_refused_in_any_order(order, state, deploy):
    ctrl = baseline_ctrl()
    ctrl.previews = [good_preview()]
    config = ordered(order, po_item(deploy=deploy), direct_child())
    status, result = run(ctrl, config, state=state)
    assert_refused(ctrl, status, result, "also requested directly")


@pytest.mark.parametrize("mode", ["trunk", "access", "routed"])
def test_any_direct_profile_for_the_claimed_member_is_a_conflict(mode):
    ctrl = baseline_ctrl()
    status, result = run(ctrl, [po_item(deploy=False), {"name": IF7, "type": "eth", "switch": [SWITCH_IP],
                                                        "deploy": False, "profile": {"mode": mode}}])
    assert_refused(ctrl, status, result, "also requested directly")


@pytest.mark.parametrize("spelling", ["eth1/7", "e1/7", "ETHERNET1/7", "Ethernet 1/7"])
def test_direct_entry_spelling_is_normalised_like_the_existing_path(spelling):
    ctrl = baseline_ctrl()
    child = direct_child()
    child["name"] = spelling
    status, result = run(ctrl, [po_item(deploy=False), child])
    assert_refused(ctrl, status, result, "also requested directly")


# ------------------------------------------------------------------ family B: a competing port-channel (PVLAN or not)
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("order", ORDERS)
def test_member_claimed_by_a_non_pvlan_port_channel_is_refused_in_any_order(order, state):
    ctrl = baseline_ctrl()
    status, result = run(ctrl, ordered(order, po_item(deploy=False), trunk_po()), state=state)
    assert_refused(ctrl, status, result, "also claimed by port-channel")


@pytest.mark.parametrize("members", [["eth1/7"], ["e1/7"], ["ETHERNET1/7"], [IF8, " Ethernet1/7 "], ["Ethernet1/8,Ethernet1/7"]])
def test_competing_claim_spelling_and_list_forms_are_normalised(members):
    ctrl = baseline_ctrl()
    status, result = run(ctrl, [po_item(deploy=False), trunk_po(members=members)])
    assert_refused(ctrl, status, result, "also claimed by port-channel")


@pytest.mark.parametrize("order", ORDERS)
def test_two_pvlan_port_channels_still_cannot_share_a_member(order):
    ctrl = baseline_ctrl()
    status, result = run(ctrl, ordered(order, po_item(deploy=False), po_item(name="po11", deploy=False)))
    assert status == "fail" and "also assigns it to port-channel" in result["msg"] and ctrl.writes() == []


@pytest.mark.parametrize("token", ["Ethernet1/5-8", "Ethernet1/7-9", "Ethernet1/x", "Port-channel3"])
def test_member_entry_that_cannot_be_resolved_is_refused_with_an_explanation(token):
    ctrl = baseline_ctrl()
    status, result = run(ctrl, [po_item(deploy=False), trunk_po(members=[token])])
    assert_refused(ctrl, status, result, "cannot be resolved")


# ------------------------------------------------------------------ the existing HAVE-based controls are kept
def test_have_based_direct_child_control_is_kept():
    ctrl = created_ctrl()
    status, result = run(ctrl, [_eth(IF7)], state="replaced")
    assert status == "fail" and "managed by the parent" in result["msg"] and ctrl.writes() == []


def test_have_based_member_in_another_port_channel_control_is_kept():
    ctrl = baseline_ctrl()
    ctrl.detail[IF7]["policy"] = "int_port_channel_trunk_member_11_1"
    status, result = run(ctrl, [po_item()])
    assert status == "fail" and "already a port-channel member" in result["msg"] and ctrl.writes() == []


# ------------------------------------------------------------------ non-conflicting changes are preserved (positive controls)
def _other_port_ctrl():
    ctrl = baseline_ctrl()
    nv = trunk_host_nv(IF8)
    ctrl.detail[IF8] = {"policy": TRUNK, "nvPairs": nv}
    return ctrl


@pytest.mark.parametrize("order", ORDERS)
def test_pvlan_po_with_a_direct_change_on_ANOTHER_port_is_unaffected(order):
    ctrl = _other_port_ctrl()
    ctrl.previews = [good_preview()]
    other = _eth(IF8)
    other["profile"]["description"] = "independent change"
    status, result = run(ctrl, ordered(order, po_item(deploy=False), other))
    assert status == "exit", result
    assert len(ctrl.creates()) == 1 and ctrl.requests("POST", "/rest/interface/modify"), "both independent writes happen"


@pytest.mark.parametrize("order", ORDERS)
def test_pvlan_po_and_a_port_channel_with_a_DIFFERENT_member_are_unaffected(order):
    ctrl = _other_port_ctrl()
    status, result = run(ctrl, ordered(order, po_item(deploy=False), trunk_po(members=[IF8])))
    assert status == "exit", result
    assert len(ctrl.creates()) == 2


def test_flows_without_a_pvlan_port_channel_get_no_new_restriction():
    # ordinary Po + a direct entry for its member and a spelling the new check cannot resolve: unchanged behaviour
    ctrl = _other_port_ctrl()
    status, result = run(ctrl, [trunk_po(members=["Ethernet1/5-8"]), direct_child(IF8)])
    assert status == "exit", result
    ctrl2 = _other_port_ctrl()
    status, result = run(ctrl2, [trunk_po(members=[IF8]), trunk_po(name="po12", members=[IF8])])
    assert status == "exit", "two ORDINARY port-channels sharing a member are not this change's business"


def test_m1_creation_and_m2_repetition_still_work():
    ctrl = baseline_ctrl()
    ctrl.previews = [good_preview()]
    status, result = run(ctrl, [po_item()])
    assert status == "exit" and result["changed"] is True and len(ctrl.creates()) == 1
    ctrl2 = created_ctrl()
    status, result = run(ctrl2, [po_item()])
    assert status == "exit" and result["changed"] is False and ctrl2.writes() == []


# ------------------------------------------------------------------ pure units: normalisation and switch identity
def test_normalize_member_list_forms():
    names, bad = P.normalize_member_list("Ethernet1/7, eth1/8 ,e1/9,ETHERNET1/10/1")
    assert names == {"ethernet1/7", "ethernet1/8", "ethernet1/9", "ethernet1/10/1"} and bad == []
    names, bad = P.normalize_member_list("Ethernet1/5-8,Port-channel3,,")
    assert names == set() and bad == ["Ethernet1/5-8", "Port-channel3"]
    assert P.normalize_member_list("") == (set(), []) and P.normalize_member_list(None) == (set(), [])


class _Stub(object):
    """An object built WITHOUT __init__ (the pattern the existing unit tests use): the check reads only self.want."""
    pvlan_blocked = None

    def __init__(self, wants):
        import types
        self.want = wants
        self.pvlan_blocked = []
        self.dcnm_intf_pvlan_block = types.MethodType(module.DcnmIntf.dcnm_intf_pvlan_block, self)
        # bound lazily: the method does not exist in the E1 product, and only THESE tests may fail there
        self.dcnm_intf_pvlan_requested_conflicts = types.MethodType(module.DcnmIntf.dcnm_intf_pvlan_requested_conflicts, self)


def _want(policy, name, sno, nv):
    return {"policy": policy, "interfaces": [{"ifName": name, "serialNumber": sno, "nvPairs": nv}]}


def test_conflicts_are_scoped_by_switch_serial():
    parent = _want(P.PO_HOST_POLICY, "Port-channel10", "SER-A", {"MEMBER_INTERFACES": "Ethernet1/7"})
    same_port_other_switch = _want("int_trunk_host", "Ethernet1/7", "SER-B", {})
    same_port_same_switch = _want("int_trunk_host", "Ethernet1/7", "SER-A", {})
    stub = _Stub([parent, same_port_other_switch])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert stub.pvlan_blocked == [], "the same port name on ANOTHER switch is not a conflict"
    stub = _Stub([same_port_same_switch, parent])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert [b["interface"] for b in stub.pvlan_blocked] == ["Ethernet1/7"]


def test_vpc_peer_members_are_matched_on_their_own_peer_serial():
    parent = _want(P.PO_HOST_POLICY, "Port-channel10", "SER-A", {"MEMBER_INTERFACES": "Ethernet1/7"})
    vpc_hit = _want("int_vpc_trunk_host", "vPC20", "SER-A~SER-B", {"PEER1_MEMBER_INTERFACES": "Ethernet1/7", "PEER2_MEMBER_INTERFACES": ""})
    vpc_peer2_other_switch = _want("int_vpc_trunk_host", "vPC21", "SER-A~SER-B", {"PEER1_MEMBER_INTERFACES": "", "PEER2_MEMBER_INTERFACES": "Ethernet1/7"})
    stub = _Stub([parent, vpc_hit])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert len(stub.pvlan_blocked) == 1
    stub = _Stub([parent, vpc_peer2_other_switch])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert stub.pvlan_blocked == [], "peer-2 members belong to the SECOND serial"


def test_no_pvlan_parent_means_no_work_and_no_blocks():
    stub = _Stub([_want("int_trunk_host", "Ethernet1/7", "SER-A", {}),
                  _want("int_port_channel_trunk_host", "Port-channel11", "SER-A", {"MEMBER_INTERFACES": "Ethernet1/5-8"})])
    stub.dcnm_intf_pvlan_requested_conflicts()
    assert stub.pvlan_blocked == []
