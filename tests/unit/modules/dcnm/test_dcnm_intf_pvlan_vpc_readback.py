"""VPC-HOST-E2-READBACK: regressions for the two readback gaps of VPC-HOST-E1 (architect review R1-01 and R1-02), with the real main().

NOT LIVE TESTED. R1-01: after the deploy, the MEMBER of a peer is compared with the member model EXPECTED for that peer (values inherited from
the frozen PRE-state), not only checked for policy/PO_ID/In-Sync. R1-02: after a deletion, the COMPLETE released member is compared with the
explicit release contract recorded in the leg (PO_RELEASED_MEMBER_NV), not only for policy/ADMIN_STATE/CONF. Same synthetic harness as the rest
of the vPC tests; the only addition is a controller that changes ONE member AFTER the deploy answer (as the architect's probes do)."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

import pytest

from .test_dcnm_intf_pvlan_harness import TRUNK, preview
from .test_dcnm_intf_pvlan_vpc_harness import (
    release_only,
    DEPLOY,
    M1,
    M2,
    SN1,
    SN2,
    VPC,
    VpcController,
    converged_previews,
    create_pending,
    create_previews,
    created_ctrl,
    delete_previews,
    member_after,
    member_running_baseline,
    po_stanza,
    run_vpc,
    vpc_del_item,
    vpc_item,
)

PEERS = [(SN1, M1, 1), (SN2, M2, 2)]


class AfterDeploy(VpcController):
    """Changes one member of one peer right AFTER the deploy answer (the architect's probe shape): `drift(nv)` edits the nvPairs in place and
    returns None, or returns the replacement value of `nvPairs` itself (for example None or a list)."""

    def __init__(self, serial=None, port=None, drift=None):
        super(AfterDeploy, self).__init__()
        self.target, self.drift = (serial, port), drift

    def __call__(self, mod, method, path, data=None):
        response = super(AfterDeploy, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(DEPLOY) and self.drift:
            serial, port = self.target
            node = self.nodes[serial][port]
            replaced = self.drift(node["nvPairs"])
            if replaced is not None:
                node["nvPairs"] = replaced["value"]
        return response


def setter(key, value):
    def apply(nv):
        nv[key] = value

    return apply


def remover(key):
    def apply(nv):
        nv.pop(key, None)

    return apply


def created_after_deploy(serial, port, drift):
    ctrl = AfterDeploy(serial, port, drift)
    ctrl.seed_baseline()
    create_previews(ctrl)
    return ctrl


# ================================================================== R1-01: the member after the deploy
@pytest.mark.parametrize("serial, port, peer", PEERS)
@pytest.mark.parametrize(
    "drift, needle",
    [
        (setter("PC_MODE", "on"), "PC_MODE is 'on', expected 'active'"),
        (setter("ADMIN_STATE", "true"), "ADMIN_STATE is 'true', expected 'false'"),
        (setter("PVLAN_MODE", "promiscuous"), "PVLAN_MODE is 'promiscuous', expected 'host'"),
        (setter("PO_ID", "port-channel99"), "is not the member of port-channel10"),
        (setter("CDP_ENABLE", "false"), "CDP_ENABLE is 'false', expected 'true'"),
        (setter("lldpTransmit", "true"), "lldpTransmit is 'true', expected 'false'"),
        (setter("LACP_RATE", "fast"), "LACP_RATE is 'fast', expected 'normal'"),
        (setter("LACP_PORT_PRIO", "100"), "LACP_PORT_PRIO is '100', expected '32768'"),
        (setter("DESC", "rewritten"), "DESC is 'rewritten', expected ''"),
        (setter("CONF", "mtu 1500"), "CONF is 'mtu 1500', expected ''"),
        (setter("PRIMARY_INTF", "vPC99"), "PRIMARY_INTF is 'vPC99', expected 'vPC10'"),
        (remover("PC_MODE"), "PC_MODE is missing"),
        (remover("ADMIN_STATE"), "ADMIN_STATE is missing"),
        (setter("PVLAN_MODE", ["host"]), "PVLAN_MODE is malformed (list)"),
        (setter("PC_MODE", {"x": 1}), "PC_MODE is malformed (dict)"),
    ],
)
def test_a_member_that_contradicts_its_model_after_the_deploy_fails_the_vpc_on_either_peer(serial, port, peer, drift, needle):
    ctrl = created_after_deploy(serial, port, drift)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail", result
    assert "peer %d (%s): member %s differs from the expected member model" % (peer, serial, port) in result["msg"] or needle in result["msg"]
    assert needle in result["msg"] and "peer %d (%s)" % (peer, serial) in result["msg"], result["msg"]
    other = [p for p in PEERS if p[2] != peer][0]
    assert "peer %d (" % other[2] not in result["msg"], "the correct peer is not blamed"
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    assert ctrl.modifies() == [] and ctrl.markdeletes() == [], "no repair write after the failed readback"


def test_the_positive_control_and_the_harmless_variations_still_succeed():
    ctrl = created_after_deploy(SN2, M2, None)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit" and result["changed"] is True and len(ctrl.deploys()) == 1

    def harmless(nv):
        nv["ADMIN_STATE"] = False  # a boolean instead of 'false'
        nv["LACP_PORT_PRIO"] = 32768  # an integer instead of '32768'
        nv["PC_MODE"] = "Active"  # case
        nv["INTF_NAME"] = "something-else"  # metadata, not a wire field of the member model
        nv["PTP"] = "true"
        nv["INTF_PTP"] = "true"
        nv.pop("CDP_ENABLE")  # an optional field that is absent takes the template default
        nv.pop("PRIMARY_INTF")  # metadata the controller may not return

    ctrl = created_after_deploy(SN2, M2, harmless)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit" and result["changed"] is True, result.get("msg")


def test_the_expectation_comes_from_the_frozen_pre_state_not_from_the_state_being_verified():
    # The member inherits its DESCRIPTION from its own pre-state (HOST 727-760). Rewriting it after the deploy must be caught: an expectation
    # rebuilt from the corrupted post-state would accept it.
    ctrl = AfterDeploy(SN2, M2, setter("DESC", ""))
    ctrl.seed_baseline()
    ctrl.nodes[SN2][M2]["nvPairs"]["DESC"] = "inherited-from-baseline"
    ctrl.vpc_previews[SN1] = [_preview(SN1, M1, None)]
    ctrl.vpc_previews[SN2] = [_preview(SN2, M2, "inherited-from-baseline")]
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and "DESC is '', expected 'inherited-from-baseline'" in result["msg"] and "peer 2 (%s)" % SN2 in result["msg"], result.get("msg")
    # and the same member, untouched, is accepted
    ctrl = AfterDeploy()
    ctrl.seed_baseline()
    ctrl.nodes[SN2][M2]["nvPairs"]["DESC"] = "inherited-from-baseline"
    ctrl.vpc_previews[SN1] = [_preview(SN1, M1, None)]
    ctrl.vpc_previews[SN2] = [_preview(SN2, M2, "inherited-from-baseline")]
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "exit", result.get("msg")


def _preview(serial, port, member_desc):
    running = member_running_baseline(port) + (["  description %s" % member_desc] if member_desc else [])
    after = member_after(port) + (["  description %s" % member_desc] if member_desc else [])
    pending = create_pending(port)
    return preview(pending, serial=serial, running=running, expected=po_stanza() + after)


def test_a_wrong_member_is_not_hidden_by_a_correct_other_peer_or_by_a_generic_in_sync():
    ctrl = created_after_deploy(SN1, M1, setter("PC_MODE", "passive"))
    # every interface keeps answering In-Sync (the harness default): that alone must not be accepted as success
    status, result = run_vpc(ctrl, [vpc_item()])
    assert (
        status == "fail"
        and "peer 1 (%s): member %s differs" % (SN1, M1) in result["msg"]
        and "In-Sync but the post-deploy intent readback differs" in result["msg"]
    )


def test_two_wrong_members_are_both_reported():
    class Both(AfterDeploy):
        def __call__(self, mod, method, path, data=None):
            response = super(Both, self).__call__(mod, method, path, data)
            if method == "POST" and path.endswith(DEPLOY):
                self.nodes[SN2][M2]["nvPairs"]["ADMIN_STATE"] = "true"
            return response

    ctrl = Both(SN1, M1, setter("PC_MODE", "passive"))
    ctrl.seed_baseline()
    create_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and "peer 1 (%s)" % SN1 in result["msg"] and "peer 2 (%s)" % SN2 in result["msg"]


def test_update_readback_judges_the_member_against_the_new_model():
    from .test_dcnm_intf_pvlan_vpc_harness import converged_preview, pc_mode_preview

    for serial, port, peer in PEERS:
        ctrl = AfterDeploy(serial, port, setter("PC_MODE", "active"))  # the controller did NOT apply the new mode on that member
        ctrl.seed_baseline().seed_vpc()
        ctrl.next_invocation()
        ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1), pc_mode_preview(SN1, M1)]
        ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2), pc_mode_preview(SN2, M2)]
        status, result = run_vpc(ctrl, [vpc_item(pc_mode="passive")], state="merged")
        assert status == "fail" and "PC_MODE is 'active', expected 'passive'" in result["msg"] and "peer %d (%s)" % (peer, serial) in result["msg"], result.get(
            "msg"
        )
        assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1 and ctrl.markdeletes() == []
    ctrl = AfterDeploy()  # positive control of the update
    ctrl.seed_baseline().seed_vpc()
    ctrl.next_invocation()
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1), pc_mode_preview(SN1, M1)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2), pc_mode_preview(SN2, M2)]
    status, result = run_vpc(ctrl, [vpc_item(pc_mode="passive")], state="merged")
    assert status == "exit" and result["changed"] is True, result.get("msg")


# ================================================================== the same coherence BEFORE any change
@pytest.mark.parametrize("serial, port, peer", PEERS)
@pytest.mark.parametrize(
    "drift, needle",
    [
        (setter("PC_MODE", "on"), "PC_MODE is 'on', expected 'active'"),
        (setter("PVLAN_MODE", "promiscuous"), "PVLAN_MODE is 'promiscuous', expected 'host'"),
        (setter("CDP_ENABLE", "false"), "CDP_ENABLE is 'false', expected 'true'"),
        (remover("PC_MODE"), "PC_MODE is missing"),
    ],
)
@pytest.mark.parametrize("flow", ["repeat", "update", "delete"])
def test_a_member_that_already_contradicts_its_model_is_refused_before_any_write(serial, port, peer, drift, needle, flow):
    ctrl = created_ctrl()
    drift(ctrl.nodes[serial][port]["nvPairs"])
    converged_previews(ctrl)
    delete_previews(ctrl)
    if flow == "delete":
        status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    else:
        item = vpc_item(peer1_description="a", peer2_description="b") if flow == "update" else vpc_item()
        status, result = run_vpc(ctrl, [item], state="merged")
    assert status == "fail" and needle in result["msg"] and "member %s differs from the expected member model" % port in result["msg"], result.get("msg")
    assert serial in result["msg"]
    assert ctrl.writes() == [], "refused before the first write"


# ================================================================== R1-02: the released member after a deletion
class Released(VpcController):
    def __init__(self, serial=None, port=None, drift=None):
        super(Released, self).__init__()
        self.target, self.drift = (serial, port), drift

    def __call__(self, mod, method, path, data=None):
        response = super(Released, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(DEPLOY) and self.drift:
            serial, port = self.target
            node = self.nodes[serial][port]
            replaced = self.drift(node["nvPairs"])
            if replaced is not None:
                node["nvPairs"] = replaced["value"]
        return response


def deleted_run(serial=None, port=None, drift=None):
    ctrl = Released(serial, port, drift)
    ctrl.seed_baseline().seed_vpc()
    ctrl.next_invocation()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    return ctrl, status, result


@pytest.mark.parametrize("serial, port, peer", PEERS)
@pytest.mark.parametrize(
    "drift, needle",
    [
        (setter("ALLOWED_VLANS", "2301"), "ALLOWED_VLANS is '2301', the release contract requires 'none'"),
        (setter("ALLOWED_VLANS", "all"), "ALLOWED_VLANS is 'all', the release contract requires 'none'"),
        (setter("NATIVE_VLAN", "5"), "NATIVE_VLAN is '5', the release contract requires ''"),
        (setter("MTU", "default"), "MTU is 'default', the release contract requires 'jumbo'"),
        (setter("BPDUGUARD_ENABLED", "true"), "BPDUGUARD_ENABLED is 'true', the release contract requires 'no'"),
        (setter("PORTTYPE_FAST_ENABLED", "false"), "PORTTYPE_FAST_ENABLED is 'false', the release contract requires 'true'"),
        (setter("DESC", "leftover"), "DESC is 'leftover', the release contract requires ''"),
        (setter("SPEED", "10Gb"), "SPEED is '10Gb', the release contract requires 'Auto'"),
        (setter("PO_ID", "port-channel10"), "residual PVLAN/channel-group field PO_ID='port-channel10'"),
        (setter("PVLAN_MODE", "host"), "residual PVLAN/channel-group field PVLAN_MODE='host'"),
        (setter("PC_MODE", "active"), "residual PVLAN/channel-group field PC_MODE='active'"),
        (remover("ALLOWED_VLANS"), "ALLOWED_VLANS is None, the release contract requires 'none'"),
        (setter("ALLOWED_VLANS", ["none"]), "ALLOWED_VLANS is ['none'], the release contract requires 'none'"),
        (setter("ADMIN_STATE", "true"), "not administratively down"),
        (setter("GUARD_MODE", "root"), "the released member's CLI model differs from the contract"),  # a modeled field outside the contract's own keys
        (setter("CDP_ENABLE", "false"), "the released member's CLI model differs from the contract"),
        (setter("ENABLE_PFC", "true"), "cannot be modeled"),  # a field the model cannot judge is never success
    ],
)
def test_a_released_member_that_diverges_from_the_contract_fails_the_deletion_on_either_peer(serial, port, peer, drift, needle):
    ctrl, status, result = deleted_run(serial, port, drift)
    assert status == "fail" and needle in result["msg"], result.get("msg")
    assert "peer %d (%s)" % (peer, serial) in result["msg"] and port in result["msg"] or "administratively down" in result["msg"]
    other = [p for p in PEERS if p[2] != peer][0]
    verification = result["pvlan_verification"][VPC]
    assert verification["state"] == "failed" and verification["peers"][other[0]] == "verified" and verification["peers"][serial] != "verified"
    release_only(ctrl)
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.deploys()) == 1 and ctrl.creates() == [], "no repair write after the deploy"


def test_the_released_baseline_and_harmless_metadata_are_still_accepted():
    ctrl, status, result = deleted_run()
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified"

    def harmless(nv):
        nv["INTF_NAME"] = "metadata"
        nv["PTP"] = "true"
        nv["ADMIN_STATE"] = False  # boolean form
        nv["ALLOWED_VLANS"] = "none"

    for serial, port, _peer in PEERS:
        ctrl, status, result = deleted_run(serial, port, harmless)
        assert status == "exit" and result["pvlan_verification"][VPC]["peers"] == {SN1: "verified", SN2: "verified"}, result.get("msg")
        assert ctrl.nodes[serial][port]["policy"] == TRUNK


def test_an_absent_nvpairs_member_still_fails_the_deletion_as_before():
    ctrl, status, result = deleted_run(SN2, M2, lambda nv: {"value": None})
    assert status == "fail" and "could not be read authoritatively" in result["msg"] and "peer 2 (%s)" % SN2 in result["msg"]
    assert result["pvlan_verification"][VPC]["state"] == "failed"
    release_only(ctrl)


def test_both_peers_released_with_divergences_are_both_reported():
    class Two(Released):
        def __call__(self, mod, method, path, data=None):
            response = super(Two, self).__call__(mod, method, path, data)
            if method == "POST" and path.endswith(DEPLOY):
                self.nodes[SN1][M1]["nvPairs"]["MTU"] = "default"
            return response

    ctrl = Two(SN2, M2, setter("ALLOWED_VLANS", "2301"))
    ctrl.seed_baseline().seed_vpc()
    ctrl.next_invocation()
    delete_previews(ctrl)
    status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "peer 1 (%s)" % SN1 in result["msg"] and "peer 2 (%s)" % SN2 in result["msg"]
    assert "MTU is 'default'" in result["msg"] and "ALLOWED_VLANS is '2301'" in result["msg"]


def test_the_message_names_peer_interface_and_field():
    ctrl, status, result = deleted_run(SN2, M2, setter("ALLOWED_VLANS", "2301"))
    assert "peer 2 (%s): member %s: ALLOWED_VLANS is '2301'" % (SN2, M2) in result["msg"]
    ctrl = created_after_deploy(SN2, M2, setter("PC_MODE", "on"))
    status, result = run_vpc(ctrl, [vpc_item()])
    assert "peer 2 (%s): member %s differs from the expected member model: PC_MODE is 'on', expected 'active'" % (SN2, M2) in result["msg"]
    assert json.dumps(result)  # the whole result stays serialisable
