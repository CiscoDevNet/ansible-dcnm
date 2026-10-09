"""VPC-HOST-E5: controls of the two corrections made after the first real cycle (L1-E4 live, 2026-10-08). NOT LIVE TESTED for E5.

F1: the created vPC parent carries `createVpc` = "true" (MEASURED A1/A2): read-only controller metadata, not a template field.
F2: the child Po of a deleted vPC is listed `interface_delete` whose source is the PARENT vPC (`vpc10`) (MEASURED F).
The fixtures come from the sanitized captures in fixtures/pvlan_vpc_l1e4_measured.json; the harness stays SIMULATED elsewhere.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P

from .test_dcnm_intf_pvlan_vpc_harness import (
    M1,
    M2,
    SN1,
    SN2,
    VPC,
    created_ctrl,
    delete_previews,
    converged_previews,
    release_only,
    run_vpc,
    vpc_del_item,
    vpc_item,
)

FX = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "pvlan_vpc_l1e4_measured.json")))


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
    from .test_dcnm_intf_pvlan_vpc_harness import converged_preview, pc_mode_preview

    sent = _updated(measured_ctrl(), (converged_preview, pc_mode_preview), vpc_item(pc_mode="passive"), "merged")
    assert sent["createVpc"] == "true" and sent["PC_MODE"] == "passive", "the controller's own metadata value travels back unchanged"


def test_a_replaced_update_of_the_measured_parent_echoes_createVpc_unchanged_never_dropped():
    from .test_dcnm_intf_pvlan_vpc_harness import PRIMARY, SECONDARY, converged_preview, update_preview

    new = 2213
    item = vpc_item(pvlan_association=[{"primary_vlan": PRIMARY, "secondary_vlan": new}])
    sent = _updated(measured_ctrl(), (converged_preview, lambda s, p: update_preview(s, p, (PRIMARY, SECONDARY), (PRIMARY, new))), item, "replaced")
    assert sent["createVpc"] == "true"


def test_creation_never_writes_createVpc_the_controller_adds_it():
    from .test_dcnm_intf_pvlan_vpc_harness import baseline_ctrl, create_previews

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
    from .test_dcnm_intf_pvlan_vpc_harness import po_stanza

    assert "  spanning-tree bpduguard enable" in po_stanza()
