"""PR725-VPC-FINAL-INTEGRATION: the batch gate (VPC-BATCH-GATE / VPC-READS) and the staged deployment (STAGED, check_deploy_resend) together.

Two PVLAN host vPCs of ONE pair are saved with ``deploy: false`` and then deployed together by one request with ``deploy: true`` and
``check_deploy: true``. The controller double is MultiVpc (test_dcnm_intf_pvlan_vpc_batch) with the MEASURED shape of a saved vPC (Beta
S1/S3b): its parent is listed with ``complianceStatus`` null and its child port-channels are Out-of-Sync until a deploy of that vPC
succeeded. Real main(); only the controller boundary and time are intercepted. Values are SYNTHETIC. NOT LIVE TESTED by this file."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from unittest.mock import patch

from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson, AnsibleFailJson, exit_json, fail_json
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from . import test_dcnm_intf_pvlan_vpc_harness as V
from . import test_dcnm_intf_pvlan_vpc_batch as B
from .dcnm_module import set_module_args


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


def run(ctrl, config, check_deploy):
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
    status, result = run(ctrl, saved, check_deploy=False)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert len(ctrl.creates()) == 1 and ctrl.deploys() == [], "stage 1 saves both intents and deploys nothing"

    deploy = copy.deepcopy(saved)
    for item in deploy:
        item["deploy"] = True
    # control: a saved vPC that is NOT in the request is still foreign; nothing is written
    next_invocation(ctrl)
    status, result = run(ctrl, deploy[:1], check_deploy=True)
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert "vPC10" in result["msg"] and "outside this deploy batch: ethernet1/11, port-channel11" in result["msg"]

    next_invocation(ctrl)
    status, result = run(ctrl, deploy, check_deploy=True)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    assert ctrl.creates() == [] and ctrl.modifies() == [], "the saved intents are not rewritten"
    assert len(ctrl.deploys()) == 1, "one deploy for both vPCs; the converged resend check sends nothing more"
    assert sorted(d["ifName"] for d in json.loads(ctrl.deploys()[0][2])) == ["vPC10", "vPC11"]
    # each vPC is judged on BOTH peers at each site; the other saved vPC's pending is its own, never foreign
    sites = sorted((g["site"], g["serial"], g["vpc"], g["targets"][g["vpc"]]) for g in result["pvlan_gate"])
    assert sites == sorted((site, s, v, decision) for site, decision in (("prior", "deploy"), ("deploy", "deploy"), ("check_deploy_resend", "converged"))
                           for v in ("vPC10", "vPC11") for s in (V.SN1, V.SN2))

    next_invocation(ctrl)
    status, result = run(ctrl, deploy, check_deploy=True)
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")
