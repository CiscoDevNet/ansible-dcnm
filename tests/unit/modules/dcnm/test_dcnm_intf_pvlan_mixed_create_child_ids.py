"""Interaction of two independent changes (mixed creation x vPC child ids): a conventional vPC and a PVLAN vPC whose peers use port-channel
numbers different from the vPC id, created in ONE call with deploy true. The PVLAN part is judged with each peer's own Po (11 / 12); the conventional
child ownership still comes from the conventional vPC's own PEERn_PCID. NOT LIVE TESTED."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

from . import test_dcnm_intf_pvlan_vpc_harness as V
from .test_dcnm_intf_pvlan_mixed_create import PATCH, V5, conv_child, conv_vpc_create_item, join_block, vpc_ctrl, vpc_owned
from .test_dcnm_intf_pvlan_vpc_child_ids import _remap_answer


def _call(extra):
    ctrl = vpc_ctrl()
    for serial, port, pcid in ((V.SN1, V.M1, "11"), (V.SN2, V.M2, "12")):
        pv = _remap_answer(V.create_preview(serial, port), pcid)
        entry = pv["DATA"][0]
        entry["pendingConfig"] = list(entry["pendingConfig"]) + list(extra.get(serial, []))
        ctrl.vpc_previews[serial] = [pv, copy.deepcopy(_remap_answer(V.converged_preview(serial, port), pcid))]
    return ctrl, V.run_vpc(ctrl, [conv_vpc_create_item(), V.vpc_item(peer1_pcid=11, peer2_pcid=12)], state="merged", patch_version=PATCH)


def test_mixed_vpc_creation_with_a_pvlan_vpc_of_other_port_channel_numbers_is_deployed_once_and_owns_only_the_conventional_pieces():
    extra = {s: conv_child() + join_block(V5, 305) for s in (V.SN1, V.SN2)}
    ctrl, (status, result) = _call(extra)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert vpc_owned(result) == [(V.SN1, ("ethernet1/5", "port-channel305")), (V.SN2, ("ethernet1/5", "port-channel305"))]
    deploys = [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]
    assert len(deploys) == 1 and sorted(i["ifName"] for i in json.loads(deploys[0][2])) == sorted(["vPC305", V.VPC])
    assert "port-channel11" in ctrl.nodes[V.SN1] and "port-channel12" in ctrl.nodes[V.SN2] and "port-channel10" not in ctrl.nodes[V.SN1]


def test_a_pending_child_of_the_pvlan_vpcs_number_on_the_wrong_peer_is_not_granted_by_the_conventional_creation():
    # the conventional creation owns port-channel305 only; a stray port-channel12 block on peer 1 is nobody's pending in this batch
    extra = {V.SN1: conv_child() + join_block(V5, 305) + conv_child(12), V.SN2: conv_child() + join_block(V5, 305)}
    ctrl, (status, result) = _call(extra)
    assert status == "fail" and "outside this deploy batch" in result["msg"], result.get("msg")
    assert not [c for c in ctrl.calls if c[0] == "POST" and c[1].endswith(V.DEPLOY)]
