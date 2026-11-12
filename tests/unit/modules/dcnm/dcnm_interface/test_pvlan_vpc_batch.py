"""Several PVLAN vPCs in one invocation, staged deployment and result identity."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import collections
import copy
import json
import pytest

from unittest.mock import patch
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleFailJson
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import exit_json
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import fail_json

from .helpers import vpc_controller as V
from .helpers.vpc_controller import MultiVpc
from .helpers.vpc_controller import PA
from .helpers.vpc_controller import PAIRS
from .helpers.vpc_controller import PB
from .helpers.vpc_controller import created
from .helpers.vpc_controller import kind_of
from .helpers.vpc_controller import post_gets
from .helpers.vpc_controller import post_kinds
from .helpers.vpc_controller import run
from .helpers.vpc_controller import same_name_on_two_pairs
from .helpers.vpc_controller import serial_of
from .helpers import vpc_controller as B
from ..dcnm_module import set_module_args
from .helpers import membership as UP


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_batch.py
# PR725 VPC-BATCH-GATE / VPC-READS: several PVLAN host vPCs of the SAME pair (and of two pairs) in ONE invocation, through the REAL main().
#
# The controller double is the existing VpcController (helpers/vpc_controller) for N vPCs over one or two pairs: vPC<k> with PCID k
# and its own members on each peer, the harness stanzas with the id substituted, previews derived from the current state of each serial
# (pending of every vPC created or deleted but not yet deployed), and post-deploy readiness / read-failure / drop / mutate injection.
# Only the transport, inventory/version helpers and time.sleep (counted, never slept) are replaced. Values are SYNTHETIC.
# NOT LIVE TESTED by this file.
# ====================================================================================================
# ------------------------------------------------------------------ VPC-BATCH-GATE
def test_two_vpcs_of_one_pair_are_created_and_deployed_in_one_invocation():
    ctrl, config = created(2)
    status, result = run(ctrl, config)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    assert sorted(d["ifName"] for d in json.loads(ctrl.deploys()[0][2])) == ["vPC10", "vPC11"]
    assert sorted((g["serial"], g["vpc"], g["targets"][g["vpc"]]) for g in result["pvlan_gate"]) == sorted(
        (s, v, "deploy") for v in ("vPC10", "vPC11") for s in (V.SN1, V.SN2))
    for k in (10, 11):
        for serial, port in ((V.SN1, "Ethernet1/%d" % k), (V.SN2, "Ethernet2/%d" % k)):
            assert ctrl.nodes[serial]["port-channel%d" % k]["source"] == "vPC%d" % k
            assert ctrl.nodes[serial][port]["policy"] == V.PO_MEMBER and ctrl.nodes[serial][port]["nvPairs"]["PO_ID"] == "port-channel%d" % k


def test_one_vpc_control_is_unchanged():
    ctrl, config = created(1)
    status, result = run(ctrl, config)
    assert status == "exit" and len(ctrl.deploys()) == 1, result.get("msg")
    assert [g["targets"]["vPC10"] for g in result["pvlan_gate"]] == ["deploy", "deploy"]


def test_two_pairs_one_vpc_each_and_two_vpcs_each():
    for n in (2, 4):
        ctrl, config = created(n, npairs=2)
        status, result = run(ctrl, config)
        assert status == "exit" and len(ctrl.deploys()) == 1, (n, result.get("msg"))


def test_several_members_per_peer():
    ctrl, config = created(2, members=2)
    status, result = run(ctrl, config)
    assert status == "exit" and len(ctrl.deploys()) == 1, result.get("msg")
    assert all(ctrl.nodes[V.SN1]["Ethernet1/%d" % p]["policy"] == V.PO_MEMBER for p in (10, 110, 11, 111))


def test_the_same_child_name_on_a_foreign_serial_is_not_in_the_batch():
    # vPC11 (PCID 11) is in the batch on pair 2; a `port-channel11` pending on pair 1 is NOT its child and stays foreign.
    ctrl = MultiVpc(2)
    config = [ctrl.add_vpc(10, 0), ctrl.add_vpc(11, 1)]
    ctrl.extra_pending[V.SN1] = ["interface port-channel11", "  description someone-else"]
    status, result = run(ctrl, config)
    assert status == "fail" and ctrl.deploys() == [], result.get("msg")
    assert "outside this deploy batch: port-channel11" in result["msg"] and "peer 1 (%s)" % V.SN1 in result["msg"]


def test_pending_of_a_third_port_channel_outside_the_batch_is_still_refused():
    ctrl, config = created(2)
    ctrl.extra_pending[V.SN2] = ["interface port-channel99", "  description foreign"]
    status, result = run(ctrl, config)
    assert status == "fail" and ctrl.deploys() == [], result.get("msg")
    assert "outside this deploy batch: port-channel99" in result["msg"]
    assert "port-channel11" not in result["msg"] and "port-channel10" not in result["msg"].split("outside this deploy batch:")[1]
    assert "Intent for these targets was ALREADY changed" in result["msg"] and "No deployment request was sent" in result["msg"]


def test_a_vpc_registered_but_not_deployed_in_this_batch_stays_foreign():
    ctrl = MultiVpc(1)
    config = [ctrl.add_vpc(10, 0), ctrl.add_vpc(11, 0, deploy=False)]
    status, result = run(ctrl, config)
    assert status == "fail" and ctrl.deploys() == [], result.get("msg")
    assert "outside this deploy batch: ethernet1/11, port-channel11" in result["msg"]


def test_a_global_command_on_one_peer_refuses_every_vpc_of_the_batch():
    ctrl, config = created(2)
    ctrl.extra_pending[V.SN2] = ["feature lacp"]
    status, result = run(ctrl, config)
    assert status == "fail" and ctrl.deploys() == [], result.get("msg")
    assert "peer 2 (%s): pending carries commands outside interface scope" % V.SN2 in result["msg"]


def test_two_vpcs_of_one_pair_are_deleted_in_one_invocation():
    ctrl, config = created(2)
    assert run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    status, result = run(ctrl, [ctrl.del_item(10), ctrl.del_item(11)], state="deleted")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    # one mark-delete per vPC, the four member release corrections BEFORE the single deploy of both vPCs (the delete gate judged both)
    assert [json.loads(c[2])[0]["ifName"] for c in ctrl.markdeletes()] == ["vPC10", "vPC11"]
    assert ctrl.order() == ["MODIFY"] * 4 + ["PREVIEW"] * 4 + ["DEPLOY"]
    assert sorted(d["ifName"] for d in json.loads(ctrl.deploys()[0][2])) == ["vPC10", "vPC11"]
    assert sorted((g["serial"], g["vpc"], g["targets"][g["vpc"]]) for g in result["pvlan_gate"]) == sorted(
        (s, v, "deploy") for v in ("vPC10", "vPC11") for s in (V.SN1, V.SN2))
    for k in (10, 11):
        assert (V.SN1 + "~" + V.SN2, "vPC%d" % k) not in ctrl.parents
        assert ctrl.nodes[V.SN1]["Ethernet1/%d" % k]["policy"] == V.TRUNK and ctrl.nodes[V.SN2]["Ethernet2/%d" % k]["policy"] == V.TRUNK
        assert result["pvlan_verification"]["vPC%d" % k]["state"] == "verified"


# ------------------------------------------------------------------ VPC-READS
# Implemented budget, per vPC pair, after the deploy: every round reads BOTH peer serials once (summary + forced bulk + policy list =
# 3 GETs per serial), until every leg of every vPC of the pair is In-Sync and readable in the same round; then ONE forced bulk of the
# pair supplies the parents (only when one of its vPCs is ready). post-deploy GETs = sum over pairs of (6 * rounds + 1).
def later(ctrl, rounds, serials, only=None):
    for _name, (k, pair, m1, m2) in ctrl.plan.items():
        for serial, ports in ((pair[0], m1), (pair[1], m2)):
            if serial in serials:
                for n in ["port-channel%d" % k] + list(ports):
                    if only is None or n in only:
                        ctrl.ready_round[(serial, n)] = rounds


@pytest.mark.parametrize("n, npairs", [(1, 1), (2, 1), (10, 1), (100, 1), (2, 2), (10, 2), (100, 2)])
def test_post_deploy_reads_grow_with_pairs_and_rounds_not_with_vpcs(n, npairs):
    ctrl, config = created(n, npairs)
    spy = []
    real = module.DcnmIntf.dcnm_intf_pvlan_vpc_verify
    with patch.object(module.DcnmIntf, "dcnm_intf_pvlan_vpc_verify", lambda self, t: (spy.append(t["name"]), real(self, t))):
        status, result = run(ctrl, config)
    assert status == "exit" and len(ctrl.deploys()) == 1, result.get("msg")
    assert sorted(spy) == sorted("vPC%d" % (10 + i) for i in range(n)), "every vPC is still judged"
    assert post_kinds(ctrl) == {"summary": 2 * npairs, "bulk": 3 * npairs, "policies": 2 * npairs}
    serials = collections.Counter(serial_of(c[1]) for c in ctrl.calls[[i for i, c in enumerate(ctrl.calls) if c[1].endswith(V.DEPLOY)][-1]:]
                                  if c[0] == "GET" and kind_of(c[1]) == "summary")
    assert serials == collections.Counter(s for p in PAIRS[:npairs] for s in p), "both peers of every pair are read"


def test_several_members_per_peer_share_the_same_reads():
    ctrl, config = created(2, members=2)
    status, result = run(ctrl, config)
    assert status == "exit", result.get("msg")
    assert post_gets(ctrl) == 7


@pytest.mark.parametrize("label, setup, rounds, waits", [
    ("both peers one wait late", lambda c: later(c, 1, (V.SN1, V.SN2)), 2, 1),
    ("one peer two waits late, the other ready", lambda c: later(c, 2, (V.SN2,)), 3, 2),
])
def test_late_convergence_costs_a_round_per_pair_not_per_vpc(label, setup, rounds, waits):
    ctrl, config = created(10)
    setup(ctrl)
    status, result = run(ctrl, config)
    assert status == "exit", (label, result.get("msg"))
    assert (post_gets(ctrl), len(ctrl.sleep_log)) == (6 * rounds + 1, waits), label


def test_a_target_that_never_converges_fails_after_six_rounds_and_names_its_peer():
    ctrl, config = created(10)
    later(ctrl, None, (V.SN2,), only={"port-channel14"})
    status, result = run(ctrl, config)
    assert status == "fail" and len(ctrl.deploys()) == 1
    assert result["msg"].startswith("vPC vPC14 was deployed but not every peer reached In-Sync")
    assert "peer 2 (%s): child is Out-of-Sync, not In-Sync" % V.SN2 in result["msg"]
    assert (post_gets(ctrl), len(ctrl.sleep_log)) == (6 * 6 + 1, 5)


# A read problem keeps the pair pending: all 6 rounds are spent (5 poll waits) before the failure; the remaining waits and GETs are the
# readers' own HTTP retries (summary and bulk retry, the policy list does not), counted apart from the poll rounds.
@pytest.mark.parametrize("kind, serial, needle, gets, waits", [
    ("summary", V.SN2, "the interface summary of %s could not be read authoritatively" % V.SN2, 48, 23),
    ("bulk", V.SN1, "the detail of port-channel10 on %s could not be read authoritatively" % V.SN1, 36, 11),
    ("policies", V.SN2, "the switch policy list of %s could not be read authoritatively" % V.SN2, 36, 5),
])
def test_an_unreadable_peer_read_is_never_resolved_with_an_earlier_answer(kind, serial, needle, gets, waits):
    ctrl, config = created(10)
    ctrl.post_fail[(kind, serial)] = 10 ** 6
    status, result = run(ctrl, config)
    assert status == "fail" and len(ctrl.deploys()) == 1 and needle in result["msg"], result.get("msg")
    assert (post_gets(ctrl), len(ctrl.sleep_log)) == (gets, waits)


def test_one_transient_http_failure_is_a_reader_retry_not_a_poll_round():
    ctrl, config = created(10)
    ctrl.post_fail[("summary", V.SN2)] = 1
    status, result = run(ctrl, config)
    assert status == "exit", result.get("msg")
    assert post_kinds(ctrl) == {"summary": 3, "bulk": 3, "policies": 2}


@pytest.mark.parametrize("attr", ["post_drop", "post_dup"])
def test_a_missing_or_duplicated_child_in_one_peer_summary_fails_that_vpc(attr):
    ctrl, config = created(10)
    getattr(ctrl, attr)[V.SN2] = {"port-channel13"}
    status, result = run(ctrl, config)
    assert status == "fail" and result["msg"].startswith("vPC vPC13 was deployed but not every peer reached In-Sync")
    assert "peer 2 (%s): child is None, not In-Sync" % V.SN2 in result["msg"]


def test_a_wrong_child_value_is_refused_even_when_in_sync():
    ctrl, config = created(10)
    ctrl.post_mutate[(V.SN2, "port-channel12")] = {"ASSOCIATION_LIST": '{"ASSOCIATION_LIST":[{"P_VLAN":"2210","S_VLAN":"2299"}]}'}
    status, result = run(ctrl, config)
    assert status == "fail" and post_gets(ctrl) == 7
    assert result["msg"].startswith("vPC vPC12 was deployed and In-Sync but the post-deploy intent readback differs")


def test_an_identical_repetition_writes_nothing_and_has_no_post_deploy_phase():
    ctrl, config = created(10)
    assert run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    first = len(ctrl.calls)
    status, result = run(ctrl, config)
    repeat = ctrl.calls[first:]
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert [c for c in repeat if c[0] != "GET"] == []


def judged(ctrl, config):
    spy = []
    real = module.DcnmIntf.dcnm_intf_pvlan_vpc_verify
    with patch.object(module.DcnmIntf, "dcnm_intf_pvlan_vpc_verify", lambda self, t: (spy.append((t["sno"], t["name"])), real(self, t))):
        status, result = run(ctrl, config)
    return status, result, spy


def test_the_same_vpc_name_on_two_pairs_is_created_and_verified_per_pair():
    ctrl, config = same_name_on_two_pairs()
    status, result, spy = judged(ctrl, config)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert sorted(spy) == [(PA, "vPC10"), (PB, "vPC10")], "each pair's vPC10 is judged once"
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    assert sorted((d["serialNumber"], d["ifName"]) for d in json.loads(ctrl.deploys()[0][2])) == [(PA, "vPC10"), (PB, "vPC10")]
    assert ctrl.parents[(PA, "vPC10")]["nvPairs"]["PEER1_PO_DESC"] == "pair-a-p1"
    assert ctrl.parents[(PB, "vPC10")]["nvPairs"]["PEER1_PO_DESC"] == "pair-b-p1"
    for (sn1, sn2), desc in ((PAIRS[0], "pair-a-p1"), (PAIRS[1], "pair-b-p1")):
        assert ctrl.nodes[sn1]["port-channel10"]["nvPairs"]["DESC"] == desc
        assert ctrl.nodes[sn1]["Ethernet1/10"]["policy"] == V.PO_MEMBER and ctrl.nodes[sn2]["Ethernet2/10"]["policy"] == V.PO_MEMBER
    # reads stay per pair and round: 2 pairs, one round each, one parent bulk each
    assert post_kinds(ctrl) == {"summary": 4, "bulk": 6, "policies": 4}


def test_a_reversed_switch_order_keeps_the_controller_pair_identity():
    # pair B written as [peer2, peer1]: the module maps it to the controller's vpc_pair_sn order (existing normalization, never re-sorted)
    ctrl = MultiVpc(2)
    a = ctrl.add_vpc(10, 0, peer1_description="pair-a-p1")
    b = ctrl.add_vpc(10, 1, peer1_description="pair-b-p1")
    b["switch"] = list(reversed(b["switch"]))
    prof = b["profile"]
    prof["peer1_members"], prof["peer2_members"] = prof["peer2_members"], prof["peer1_members"]
    prof["peer2_description"] = prof.pop("peer1_description")
    status, result, spy = judged(ctrl, [a, b])
    assert status == "exit", result.get("msg")
    assert sorted(spy) == [(PA, "vPC10"), (PB, "vPC10")]
    assert ctrl.parents[(PB, "vPC10")]["nvPairs"]["PEER1_PO_DESC"] == "pair-b-p1"
    assert ctrl.nodes[PAIRS[1][0]]["port-channel10"]["nvPairs"]["DESC"] == "pair-b-p1"


def test_a_wrong_parent_on_one_pair_fails_naming_that_pair_only():
    ctrl, config = same_name_on_two_pairs()
    ctrl.post_mutate_parent[(PB, "vPC10")] = {"PEER1_PO_DESC": "pair-a-p1"}  # pair B reads back pair A's value
    status, result, spy = judged(ctrl, config)
    assert status == "fail" and len(ctrl.deploys()) == 1, result.get("msg")
    assert result["msg"].startswith("vPC vPC10 was deployed and In-Sync but the post-deploy intent readback differs")
    assert "parent PEER1_PO_DESC on %s" % PB in result["msg"] and not any(s in result["msg"] for s in PAIRS[0])
    assert spy == [(PA, "vPC10"), (PB, "vPC10")], "pair A passed with its own data before pair B failed"


def test_a_wrong_peer_on_one_pair_fails_naming_that_pair_and_peer():
    ctrl, config = same_name_on_two_pairs()
    ctrl.post_mutate[(PAIRS[1][1], "port-channel10")] = {"ASSOCIATION_LIST": '{"ASSOCIATION_LIST":[{"P_VLAN":"2210","S_VLAN":"2299"}]}'}
    status, result, _spy = judged(ctrl, config)
    assert status == "fail", result.get("msg")
    assert result["msg"].startswith("vPC vPC10 was deployed and In-Sync")
    assert "peer 2 (%s)" % PAIRS[1][1] in result["msg"]
    assert not any(s in result["msg"] for s in PAIRS[0]), "pair A's serials never appear in pair B's failure"


# a pair that never converges gets no parent bulk (only a pair with a ready vPC does): 7 + 6 * 6
@pytest.mark.parametrize("rounds, status, gets, waits", [(2, "exit", (6 * 1 + 1) + (6 * 3 + 1), 2), (None, "fail", (6 * 1 + 1) + 6 * 6, 5)])
def test_a_late_pair_never_replaces_the_other_pairs_snapshots(rounds, status, gets, waits):
    ctrl, config = same_name_on_two_pairs()
    for serial, port in ((PAIRS[1][0], "Ethernet1/10"), (PAIRS[1][1], "Ethernet2/10")):
        ctrl.ready_round[(serial, "port-channel10")] = rounds
        ctrl.ready_round[(serial, port)] = rounds
    got, result, _spy = judged(ctrl, config)
    assert got == status, result.get("msg")
    # pair A finishes in round 1 and is never read again; pair B is read every round until it finishes (or the 6 rounds end)
    assert (post_gets(ctrl), len(ctrl.sleep_log)) == (gets, waits)
    post = ctrl.calls[[i for i, c in enumerate(ctrl.calls) if c[1].endswith(V.DEPLOY)][-1]:]
    summaries = collections.Counter(serial_of(c[1]) for c in post if c[0] == "GET" and kind_of(c[1]) == "summary")
    assert summaries[PAIRS[0][0]] == summaries[PAIRS[0][1]] == 1
    assert summaries[PAIRS[1][0]] == summaries[PAIRS[1][1]] == (3 if rounds else 6)
    if status == "fail":
        assert result["msg"].startswith("vPC vPC10 was deployed but not every peer reached In-Sync")
        assert "peer 1 (%s)" % PAIRS[1][0] in result["msg"] and not any(s in result["msg"] for s in PAIRS[0])


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_batch_staged.py
# : the batch gate (VPC-BATCH-GATE / VPC-READS) and the staged deployment (STAGED, check_deploy_resend) together.
#
# Two PVLAN host vPCs of ONE pair are saved with ``deploy: false`` and then deployed together by one request with ``deploy: true`` and
# ``check_deploy: true``. The controller double is MultiVpc (test_pvlan_vpc_batch) with the MEASURED shape of a saved vPC (live
# S1/S3b): its parent is listed with ``complianceStatus`` null and its child port-channels are Out-of-Sync until a deploy of that vPC
# succeeded. Real main(); only the controller boundary and time are intercepted. Values are SYNTHETIC. NOT LIVE TESTED by this file.
# ====================================================================================================
class SavedMulti(B.MultiVpc):
    """MultiVpc whose vPCs that were saved but never deployed list their parent with complianceStatus null and their child Po
    Out-of-Sync (`deployed_vpcs` survives invocations)."""

    def _peer_summary(self, serial):
        out = super(SavedMulti, self)._peer_summary(serial)
        saved = [key for key in self.parents if key not in self.deployed_vpcs]
        children = set("port-channel%d" % self.plan[key][0] for key in saved)
        for e in out:
            if e.get("ifType") == "INTERFACE_VPC" and (e["serialNo"], e["ifName"]) in saved:
                e["complianceStatus"] = None
            elif e.get("ifName", "").lower() in children:
                e["complianceStatus"] = "Out-of-Sync"
        return out


def vpc_batch_staged_run(ctrl, config, check_deploy):
    """B.run with check_deploy chosen by the test (B.run fixes it to False)."""
    inv = dict((B.IPS[sn], {"logicalName": "sw-%s" % sn[-1], "serialNumber": sn, "isVpcConfigured": "True", "vpcDomain": 10 + i // 2,
                            "switchRole": "leaf", "managable": "True"}) for i, sn in enumerate(sorted(ctrl.nodes)))
    args = {"state": "merged", "fabric": V.FABRIC, "config": config, "check_deploy": check_deploy}
    patches = [
        patch.object(basic.AnsibleModule, "exit_json", exit_json),
        patch.object(basic.AnsibleModule, "fail_json", fail_json),
        patch.object(module, "get_fabric_inventory_details", return_value=inv),
        patch.object(module, "get_ip_sn_dict", return_value=(dict((ip, v["serialNumber"]) for ip, v in inv.items()), {})),
        patch.object(module, "dcnm_get_ip_addr_info", side_effect=lambda m, sw, a, b: sw),
        patch.object(module, "dcnm_version_supported", return_value=(12, V.NDFC)),
        patch.object(module, "dcnm_send", side_effect=ctrl),
        patch.object(module, "dcnm_get_bulk_api_support", return_value=True),
        patch.object(module, "get_fabric_details", return_value={"nvPairs": {"HOST_INTF_ADMIN_STATE": "false"}}),
        patch.object(module.time, "sleep", side_effect=ctrl.sleep_log.append),
    ]
    for p in patches:
        p.start()
    try:
        set_module_args(args)
        try:
            module.main()
        except AnsibleExitJson as exc:
            return "exit", exc.args[0]
        except AnsibleFailJson as exc:
            return "fail", exc.args[0]
        raise AssertionError("main() returned without exit_json/fail_json")
    finally:
        for p in reversed(patches):
            p.stop()


def next_invocation(ctrl):
    ctrl.next_invocation()
    ctrl.calls = []


def test_two_saved_vpcs_of_one_pair_are_deployed_together_with_check_deploy():
    ctrl = SavedMulti(1)
    saved = [ctrl.add_vpc(10, deploy=False), ctrl.add_vpc(11, deploy=False)]
    status, result = vpc_batch_staged_run(ctrl, saved, check_deploy=False)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == [], "stage 1 saves both intents and deploys nothing"

    deploy = copy.deepcopy(saved)
    for item in deploy:
        item["deploy"] = True
    # control: a saved vPC that is NOT in the request is still foreign; nothing is written
    next_invocation(ctrl)
    status, result = vpc_batch_staged_run(ctrl, deploy[:1], check_deploy=True)
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert "vPC10" in result["msg"] and "outside this deploy batch: ethernet1/11, port-channel11" in result["msg"]

    next_invocation(ctrl)
    status, result = vpc_batch_staged_run(ctrl, deploy, check_deploy=True)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.creates() == [] and ctrl.modifies() == [], "the saved intents are not rewritten"
    assert len(ctrl.deploys()) == 1, "one deploy for both vPCs; the converged resend check sends nothing more"
    assert sorted(d["ifName"] for d in json.loads(ctrl.deploys()[0][2])) == ["vPC10", "vPC11"]
    # each vPC is judged on BOTH peers at each site; the other saved vPC's pending is its own, never foreign
    sites = sorted((g["site"], g["serial"], g["vpc"], g["targets"][g["vpc"]]) for g in result["pvlan_gate"])
    assert sites == sorted((site, s, v, decision) for site, decision in (("prior", "deploy"), ("deploy", "deploy"), ("check_deploy_resend", "converged"))
                           for v in ("vPC10", "vPC11") for s in (V.SN1, V.SN2))

    next_invocation(ctrl)
    status, result = vpc_batch_staged_run(ctrl, deploy, check_deploy=True)
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_staged_deploy.py
# : a PVLAN host vPC deployed in two stages, and check_deploy on a vPC creation/update.
#
# A  (MEASURED live, S3b/S3d, NDFC 12.6.0.267): a vPC created with ``deploy: false`` (intent saved, nothing on the devices) could not be
#    continued with ``deploy: true``: the pre-write gate judged the saved creation as a deployed baseline (no Po on the device, the member still
#    a standalone trunk) and refused, and the code stated that completing an unapplied vPC was not implemented.
# B  (MEASURED live, S3j): ``check_deploy: true`` on a vPC creation converged, then the safety re-deploy gate (check_deploy_resend)
#    judged the vPC again with the creation rule "every peer must still need a deploy" and failed although the deploy had converged.
#
# The never-deployed vPC parent is listed with ``complianceStatus`` null (MEASURED, live S1/S3b); the children report Out-of-Sync before the
# deploy. Previews: the harness creation/converged stanzas (members down, H1 shape) and the MEASURED up-member vPC previews of
# fixtures/pvlan_admin_state.json (pre/post deploy). Real main(); only the controller boundary and time are intercepted.
# NOT LIVE TESTED by this file.
# ====================================================================================================
class Staged(V.VpcController):
    """VpcController whose vPC parent is listed with complianceStatus null and whose children are Out-of-Sync until a deploy succeeded
    (MEASURED shape of a saved, not yet deployed vPC); `applied` survives invocations, `deployed` (harness) does not."""

    def __init__(self):
        super(Staged, self).__init__()
        self.applied = False

    def _peer_summary(self, serial):
        out = super(Staged, self)._peer_summary(serial)
        if not self.applied:
            for e in out:
                if e.get("ifType") == "INTERFACE_VPC":
                    e["complianceStatus"] = None
                elif e.get("ifName", "").lower().startswith("port-channel"):
                    e["complianceStatus"] = "Out-of-Sync"
        return out

    def __call__(self, mod, method, path, data=None):
        resp = super(Staged, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(V.DEPLOY) and resp.get("RETURN_CODE") == 200:
            self.applied = True
        return resp


def vpc_staged_run(ctrl, config, state="merged", check_deploy=True):
    """V.run_vpc with check_deploy chosen by the test (the harness fixes it to False)."""
    args = {"state": state, "fabric": V.FABRIC, "config": config, "check_deploy": check_deploy}
    patches = [
        patch.object(basic.AnsibleModule, "exit_json", exit_json),
        patch.object(basic.AnsibleModule, "fail_json", fail_json),
        patch.object(module, "get_fabric_inventory_details", return_value=copy.deepcopy(V.INVENTORY)),
        patch.object(module, "get_ip_sn_dict", return_value=({V.IP1: V.SN1, V.IP2: V.SN2}, {})),
        patch.object(module, "dcnm_get_ip_addr_info", side_effect=lambda m, sw, a, b: sw),
        patch.object(module, "dcnm_version_supported", return_value=(12, V.NDFC)),
        patch.object(module, "dcnm_send", side_effect=ctrl),
        patch.object(module, "dcnm_get_bulk_api_support", return_value=True),
        patch.object(module, "get_fabric_details", return_value={"nvPairs": {"HOST_INTF_ADMIN_STATE": "false"}}),
        patch.object(module.time, "sleep", return_value=None),
    ]
    for p in patches:
        p.start()
    try:
        set_module_args(args)
        try:
            module.main()
        except AnsibleExitJson as exc:
            return "exit", exc.args[0]
        except AnsibleFailJson as exc:
            return "fail", exc.args[0]
        raise AssertionError("main() returned without exit_json/fail_json")
    finally:
        for p in reversed(patches):
            p.stop()


def down_create(serial):
    return V.create_preview(serial, V.M1 if serial == V.SN1 else V.M2)


def down_converged(serial):
    return V.converged_preview(serial, V.M1 if serial == V.SN1 else V.M2)


def up_create(serial):
    return UP.vpc_preview(serial, V.M1 if serial == V.SN1 else V.M2, phase="pre_deploy", serial_fx=UP.LEAF_B if serial == V.SN1 else UP.LEAF_A)


def up_converged(serial):
    return UP.vpc_preview(serial, V.M1 if serial == V.SN1 else V.M2, phase="post_deploy", serial_fx=UP.LEAF_B if serial == V.SN1 else UP.LEAF_A)


FORMS = {"down": (down_create, down_converged), "up": (up_create, up_converged)}


def ctrl_for(form):
    ctrl = Staged().seed_baseline()
    if form == "up":
        UP.up_peers(ctrl)
    return ctrl


def queue(ctrl, *makers):
    for serial in (V.SN1, V.SN2):
        ctrl.vpc_previews[serial] = [make(serial) for make in makers]


def saved_not_applied(form, state="merged"):
    """Stage 1, through main(): the vPC is created with deploy false (one create, no deploy, no preview)."""
    ctrl = ctrl_for(form)
    status, result = vpc_staged_run(ctrl, [V.vpc_item(deploy=False)], state=state, check_deploy=False)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == [] and ctrl.previews_asked() == []
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl


# ================================================================== B: check_deploy on a creation / an update
@pytest.mark.parametrize("form", ["down", "up"])
def test_b_creation_with_check_deploy_accepts_the_converged_resend_check(form):
    ctrl = ctrl_for(form)
    create, converged = FORMS[form]
    queue(ctrl, create, converged)  # deploy gate, then the check_deploy_resend gate after the accepted deploy
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1, "converged at the resend check: no second deploy"
    sites = [(g["site"], g["targets"]["vPC10"]) for g in result["pvlan_gate"]]
    assert sites == [("deploy", "deploy")] * 2 + [("check_deploy_resend", "converged")] * 2


def test_b_a_straggler_peer_after_the_deploy_is_resent_once():
    ctrl = ctrl_for("down")
    ctrl.vpc_previews[V.SN1] = [down_create(V.SN1), down_converged(V.SN1)]
    ctrl.vpc_previews[V.SN2] = [down_create(V.SN2), down_create(V.SN2)]  # peer 2 not applied yet at the resend check
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "exit", result.get("msg")
    assert len(ctrl.deploys()) == 2, "the safety re-deploy still covers a peer that the first deploy did not apply"


def test_b_foreign_pending_at_the_resend_check_is_still_refused():
    ctrl = ctrl_for("down")
    queue(ctrl, down_create, down_converged)
    entry = ctrl.vpc_previews[V.SN2][1]["DATA"][0]
    entry["pendingConfig"] += ["interface port-channel99", "  description foreign", "configure terminal"]
    entry["status"] = "Out-of-Sync"  # a pending makes the peer Out-of-Sync (an In-Sync status with a pending is refused on its own)
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1, result.get("msg")
    assert "check_deploy_resend" in result["msg"] and "outside this deploy batch: port-channel99" in result["msg"]


def test_b_an_unreadable_peer_at_the_resend_check_is_still_refused():
    ctrl = ctrl_for("down")
    queue(ctrl, down_create, down_converged)
    ctrl.vpc_previews[V.SN2][1] = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1, result.get("msg")
    assert "check_deploy_resend" in result["msg"]


def test_b_no_convergence_after_the_deploy_still_fails():
    ctrl = ctrl_for("down")
    queue(ctrl, down_create, down_converged)
    ctrl.compliance_by[(V.SN2, "port-channel10")] = "Out-of-Sync"
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1, result.get("msg")
    assert "In-Sync" in result["msg"]


def test_b_an_update_with_check_deploy_accepts_the_converged_resend_check():
    ctrl = V.created_ctrl()
    ctrl.vpc_previews[V.SN1] = [V.converged_preview(V.SN1, V.M1), V.description_preview(V.SN1, V.M1, None, "a1-peer1"),
                                V.converged_preview(V.SN1, V.M1, desc="a1-peer1")]
    ctrl.vpc_previews[V.SN2] = [V.converged_preview(V.SN2, V.M2), V.converged_preview(V.SN2, V.M2), V.converged_preview(V.SN2, V.M2)]
    status, result = vpc_staged_run(ctrl, [V.vpc_item(peer1_description="a1-peer1")])
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1


def test_b_an_identical_repetition_with_check_deploy_writes_nothing():
    ctrl = V.created_ctrl()
    queue(ctrl, down_converged)
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


# ================================================================== A: deploy false, then deploy true
@pytest.mark.parametrize("state", ["merged", "replaced"])
@pytest.mark.parametrize("form", ["down", "up"])
def test_a_a_saved_vpc_is_completed_by_the_next_deploy_true(form, state):
    ctrl = saved_not_applied(form, state)
    create, converged = FORMS[form]
    queue(ctrl, create, create, converged)  # pre-write check of the saved creation, deploy gate, resend check
    status, result = vpc_staged_run(ctrl, [V.vpc_item()], state=state)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.creates() == [] and ctrl.modifies() == [] and len(ctrl.deploys()) == 1, "no intent rewrite, exactly one deploy"
    assert [d["ifName"] for d in json.loads(ctrl.deploys()[0][2])] == ["vPC10"]
    sites = [(g["site"], g["targets"]["vPC10"]) for g in result["pvlan_gate"]]
    assert sites == [("prior", "deploy")] * 2 + [("deploy", "deploy")] * 2 + [("check_deploy_resend", "converged")] * 2
    # the next identical run is a no-op on a deployed baseline
    ctrl.next_invocation()
    ctrl.calls = []
    queue(ctrl, converged)
    status, result = vpc_staged_run(ctrl, [V.vpc_item()], state=state)
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")


def test_a_without_check_deploy_the_saved_vpc_is_deployed_once():
    ctrl = saved_not_applied("down")
    queue(ctrl, down_create, down_create)
    status, result = vpc_staged_run(ctrl, [V.vpc_item()], check_deploy=False)
    assert status == "exit" and len(ctrl.deploys()) == 1 and ctrl.creates() == [] and ctrl.modifies() == [], result.get("msg")


def test_a_a_repeated_deploy_false_writes_nothing():
    ctrl = saved_not_applied("down")
    status, result = vpc_staged_run(ctrl, [V.vpc_item(deploy=False)], check_deploy=False)
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")


def test_a_foreign_pending_on_a_peer_refuses_before_any_write():
    ctrl = saved_not_applied("down")
    queue(ctrl, down_create, down_create, down_converged)
    ctrl.vpc_previews[V.SN1][0]["DATA"][0]["pendingConfig"] += ["interface port-channel99", "  description foreign", "configure terminal"]
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert "outside this deploy batch: port-channel99" in result["msg"]


def test_a_one_peer_already_applied_is_a_partial_state_and_refused():
    ctrl = saved_not_applied("down")
    ctrl.vpc_previews[V.SN1] = [down_converged(V.SN1)]
    ctrl.vpc_previews[V.SN2] = [down_create(V.SN2)]
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert "peer 1 is already converged" in result["msg"]


def test_a_an_unreadable_peer_preview_refuses_before_any_write():
    ctrl = saved_not_applied("down")
    queue(ctrl, down_create)
    ctrl.vpc_previews[V.SN2][0] = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


def test_a_a_pending_that_shuts_an_up_member_is_refused_before_any_write():
    ctrl = saved_not_applied("up")
    queue(ctrl, up_create)
    UP.shut_the_member({"pending": ctrl.vpc_previews[V.SN1][0]["DATA"][0]["pendingConfig"]})  # the same list, changed in place
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


def test_a_a_changed_request_on_a_saved_vpc_stays_refused_before_any_write():
    ctrl = saved_not_applied("down")
    queue(ctrl, down_create)
    status, result = vpc_staged_run(ctrl, [V.vpc_item(peer1_description="changed")])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


def test_a_the_controller_parent_deployed_but_peers_not_converged_is_not_a_saved_creation():
    # the parent already reports a compliance value: the vPC was deployed once; a missing Po on the device is a drift, not a creation
    ctrl = saved_not_applied("down")
    ctrl.applied = True
    queue(ctrl, down_create)
    status, result = vpc_staged_run(ctrl, [V.vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_result_identity.py
# PR725 RESULT-IDENTITY: `pvlan_verification` keeps one entry per vPC even when the SAME vPC name is deleted on two pairs.
#
# Before: the result was keyed by the vPC name alone, so vPC10 of pair A and vPC10 of pair B overwrote each other (the judgement inside the
# module already tells them apart; only the presentation lost one). Now a name that is unique in the invocation keeps its plain key and entry
# format; a repeated name is keyed `<name>@<pair>` (pair = both peer serials, alphabetical) with `vpc` and `pair` inside the entry.
# Same controller double and entry point as test_pvlan_vpc_batch (the REAL main()). Values are SYNTHETIC. NOT LIVE TESTED.
# ====================================================================================================
A_PAIR = "~".join(sorted(B.PAIRS[0]))
B_PAIR = "~".join(sorted(B.PAIRS[1]))
KEY_A, KEY_B = "vPC10@" + A_PAIR, "vPC10@" + B_PAIR


def deleted_same_name(reverse_b=False, fail=None):
    ctrl, config = B.same_name_on_two_pairs()
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.sleep_log[:] = []
    if fail:
        fail(ctrl)
    items = [ctrl.del_item(10, 0), ctrl.del_item(10, 1)]
    if reverse_b:
        items[1]["switch"] = list(reversed(items[1]["switch"]))
    status, result = B.run(ctrl, items, state="deleted")
    return ctrl, status, result


def test_the_same_vpc_name_on_two_pairs_keeps_both_results():
    ctrl, status, result = deleted_same_name()
    assert status == "exit", result.get("msg")
    ver = result["pvlan_verification"]
    assert sorted(ver) == sorted([KEY_A, KEY_B]), "one entry per pair, no plain vPC10 entry that could read as both"
    for key, pair, vpc_pair in ((KEY_A, A_PAIR, B.PAIRS[0]), (KEY_B, B_PAIR, B.PAIRS[1])):
        entry = ver[key]
        assert entry["vpc"] == "vPC10" and entry["pair"] == pair and entry["state"] == "verified" and entry["parent"] == "not listed"
        assert sorted(entry["peers"]) == sorted(vpc_pair), "every peer of THIS pair, none of the other"
        assert set(entry["peers"].values()) == {"verified"}


def test_one_good_pair_and_one_failed_pair_are_both_reported_and_the_run_still_fails():
    def member_stuck(ctrl):
        ctrl.ready_round[(B.PAIRS[1][1], "Ethernet2/10")] = None
    ctrl, status, result = deleted_same_name(fail=member_stuck)
    assert status == "fail" and "vPC vPC10 was deleted but its release could not be verified" in result["msg"]
    assert B.PAIRS[1][1] in result["msg"] and not any(s in result["msg"] for s in B.PAIRS[0])
    ver = result["pvlan_verification"]
    assert sorted(ver) == sorted([KEY_A, KEY_B])
    assert ver[KEY_A]["state"] == "verified" and set(ver[KEY_A]["peers"].values()) == {"verified"}
    assert ver[KEY_B]["state"] == "failed"
    assert ver[KEY_B]["peers"][B.PAIRS[1][0]] == "verified" and ver[KEY_B]["peers"][B.PAIRS[1][1]] != "verified"


def test_an_unreadable_peer_fails_both_entries_and_keeps_both():
    ctrl, status, result = deleted_same_name(fail=lambda c: c.post_fail.__setitem__(("summary", B.PAIRS[1][1]), 10 ** 6))
    assert status == "fail"
    ver = result["pvlan_verification"]
    assert sorted(ver) == sorted([KEY_A, KEY_B]) and ver[KEY_A]["state"] == "verified" and ver[KEY_B]["state"] == "failed"


def test_the_identity_does_not_depend_on_the_order_of_the_peers():
    _c1, _s1, plain = deleted_same_name()
    _c2, _s2, reversed_ = deleted_same_name(reverse_b=True)
    assert sorted(reversed_["pvlan_verification"]) == sorted(plain["pvlan_verification"]) == sorted([KEY_A, KEY_B])
    assert reversed_["pvlan_verification"][KEY_B]["pair"] == B_PAIR
    assert sorted(reversed_["pvlan_verification"][KEY_B]["peers"]) == sorted(B.PAIRS[1])


def test_the_unique_name_keeps_its_plain_key_and_format():
    ctrl, config = B.created(3)
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    status, result = B.run(ctrl, [ctrl.del_item(k) for k in (10, 11, 12)], state="deleted")
    assert status == "exit", result.get("msg")
    ver = result["pvlan_verification"]
    assert sorted(ver) == ["vPC10", "vPC11", "vPC12"]
    assert all(sorted(e) == ["parent", "peers", "state"] for e in ver.values()), "no new field when the name is unique"


def test_two_different_names_on_two_pairs_keep_plain_keys():
    ctrl = B.MultiVpc(2)
    config = [ctrl.add_vpc(10, 0), ctrl.add_vpc(11, 1)]
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    status, result = B.run(ctrl, [ctrl.del_item(10, 0), ctrl.del_item(11, 1)], state="deleted")
    assert status == "exit", result.get("msg")
    assert sorted(result["pvlan_verification"]) == ["vPC10", "vPC11"]


def test_only_the_repeated_name_is_composite_when_others_are_unique():
    ctrl = B.MultiVpc(2)
    config = [ctrl.add_vpc(10, 0), ctrl.add_vpc(10, 1), ctrl.add_vpc(11, 0)]
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    status, result = B.run(ctrl, [ctrl.del_item(10, 0), ctrl.del_item(10, 1), ctrl.del_item(11, 0)], state="deleted")
    assert status == "exit", result.get("msg")
    assert sorted(result["pvlan_verification"]) == sorted([KEY_A, KEY_B, "vPC11"])
    assert "vpc" not in result["pvlan_verification"]["vPC11"]


def test_the_reads_the_writes_and_the_deploy_do_not_change():
    ctrl, status, result = deleted_same_name()
    assert status == "exit"
    # one round per pair, the summary of each peer only (no parent/peer bulk, no policy list after the deploy); one mark-delete per vPC;
    # the release modifies come before the single deploy. The composite keys add no request.
    assert B.post_kinds(ctrl) == {"summary": 4}
    assert len(ctrl.markdeletes()) == 2 and len(ctrl.deploys()) == 1 and ctrl.sleep_log == []
    assert ctrl.order() == ["MODIFY"] * 4 + ["PREVIEW"] * 4 + ["DEPLOY"]
