"""Post-deploy verification reads of PVLAN port-channels and vPCs."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import pytest

from unittest.mock import patch
from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleFailJson
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import exit_json
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import fail_json
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from ..dcnm_module import set_module_args
from .helpers.ethernet_controller import FABRIC
from .helpers.ethernet_controller import NDFC
from .helpers.ethernet_controller import PVLAN
from .helpers.ethernet_controller import TRANSITIONS
from .helpers.ethernet_controller import ok
from .helpers import vpc_controller as B
from .helpers import vpc_controller as V
from .helpers.vpc_controller import SN1
from .helpers.vpc_controller import SN2
from .helpers.vpc_controller import VPC
from .helpers.vpc_controller import created_ctrl
from .helpers.vpc_controller import delete_previews
from .helpers.vpc_controller import run_vpc
from .helpers.vpc_controller import vpc_del_item


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_r2_batch.py
# : read planning of the PVLAN post-deploy verifier (dcnm_intf_pvlan_verify_after_deploy).
#
# The REAL method runs on a REAL DcnmIntf; only the external boundary is replaced: dcnm_send by a serial-routed controller double that
# records every request before answering it, and time.sleep by a counter. Counts are of the HTTP GETs the module itself sends through
# its own readers (dcnm_intf_get_have_all_with_sno -> summary, dcnm_intf_bulk_fetch_intf_info -> bulk, dcnm_intf_get_intf_info ->
# individual), not of calls to a stub. vPC targets and released members keep their own verifiers; here they are observed through spies
# so that their position, number of calls and requests are asserted, while their behavior stays covered by the existing vPC/Po suites.
# NOT LIVE TESTED: offline request counts only, no controller latency claim.
# ====================================================================================================
SN_A, SN_B = "SAL1819SAN8", "SAL1819SAN9"
IP_A, IP_B = "10.0.0.1", "10.0.0.2"
PO_POLICY = "int_port_channel_pvlan_host"
SPEC = dict(
    fabric=dict(required=True, type="str"),
    config=dict(required=False, type="list", elements="dict", default=[]),
    deploy=dict(required=False, type="bool", default=True),
    state=dict(type="str", default="merged"),
    override_intf_types=dict(required=False, type="list", elements="str", default=[]),
    check_deploy=dict(type="bool", default=False),
    patch_version=dict(required=False, type="str", default=None),
)


def eth_nv(ifname):
    nv = copy.deepcopy(TRANSITIONS["TU2"]["post_nv"])
    nv["INTF_NAME"] = ifname
    return nv


def po_nv(ifname, member):
    return {"PVLAN_MODE": "host", "ASSOCIATION_LIST": '{"ASSOCIATION_LIST":[{"P_VLAN":"2410","S_VLAN":"2412"}]}', "MAPPING_LIST": "",
            "PVLAN_NATIVE_VLAN": "", "PVLAN_ALLOWED_VLANS": "", "ADMIN_STATE": "false", "SPEED": "Auto", "PORT_DUPLEX_MODE": "auto",
            "CONF": "", "MEMBER_INTERFACES": member, "PO_ID": ifname}


class BatchController(object):
    """Serial-routed NDFC double. ports: {serial: {ifName: [policy, nvPairs]}} (what the bulk and individual reads return).
    status: {(serial, ifName): [status, ...]} consumed one per summary read of that serial (then 'In-Sync').
    failures: {(kind, serial): [bool, ...]} consumed one per GET of that kind (True -> HTTP 500).
    summary_hook: {serial: callable(entries) -> entries} to shape one summary answer (missing / duplicate / malformed)."""

    def __init__(self, ports):
        self.ports = ports
        self.calls = []
        self.status = {}
        self.failures = {}
        self.summary_hook = {}

    @staticmethod
    def kind(path):
        if "/rest/interface/detail?serialNumber=" in path:
            return "summary"
        if "/rest/interface?serialNumber=" in path:
            return "individual" if "&ifName=" in path else "bulk"
        return "other"

    @staticmethod
    def serial(path):
        return path.split("serialNumber=")[1].split("&")[0] if "serialNumber=" in path else None

    def count(self, kind, serial=None):
        return len([c for c in self.calls if c[0] == "GET" and self.kind(c[1]) == kind and (serial is None or self.serial(c[1]) == serial)])

    def writes(self):
        return [c for c in self.calls if c[0] != "GET"]

    def __call__(self, mod, method, path, data=None):
        self.calls.append((method, path))
        kind, sn = self.kind(path), self.serial(path)
        queue = self.failures.get((kind, sn))
        if queue and queue.pop(0):
            return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
        ports = self.ports.get(sn, {})
        if kind == "summary":
            entries = []
            for name in sorted(ports):
                q = self.status.get((sn, name))
                entries.append({"ifName": name, "serialNo": sn, "fabricName": FABRIC, "ifType": "INTERFACE_ETHERNET", "isPhysical": "True",
                                "markDeleted": "False", "alias": "", "deleteReason": None,
                                "complianceStatus": q.pop(0) if q else "In-Sync",
                                "underlayPolicies": [{"templateName": ports[name][0], "entityName": name, "serialNumber": sn}]})
            hook = self.summary_hook.get(sn)
            return ok(hook(entries) if hook else entries)
        if kind == "bulk":
            return ok([{"policy": p, "interfaces": [{"serialNumber": sn, "ifName": n, "nvPairs": copy.deepcopy(nv)}]}
                       for n, (p, nv) in sorted(ports.items())])
        if kind == "individual":
            name = path.split("&ifName=")[1]
            if name not in ports:
                return ok([])
            p, nv = ports[name]
            return ok([{"policy": p, "interfaces": [{"serialNumber": sn, "ifName": name, "nvPairs": copy.deepcopy(nv)}]}])
        return ok({})


class Sleep(object):
    def __init__(self):
        self.calls = []

    def __call__(self, seconds):
        self.calls.append(seconds)


def make_intf(ctrl, sleep, ip_sn=None):
    """A real DcnmIntf built as main() builds it, inventory reduced to the switches of the test."""
    set_module_args({"state": "merged", "fabric": FABRIC, "config": []})
    with patch.object(module, "dcnm_version_supported", return_value=(12, NDFC)), patch.object(module, "dcnm_send", side_effect=ctrl), \
            patch.object(module, "get_fabric_details", return_value={"nvPairs": {"HOST_INTF_ADMIN_STATE": "false"}}):
        intf = module.DcnmIntf(basic.AnsibleModule(argument_spec=SPEC, supports_check_mode=True))
    intf.ip_sn = dict(ip_sn or {IP_A: SN_A, IP_B: SN_B})
    intf.pvlan_targets = {}
    return intf


def add_target(intf, serial, name, kind=None, policy=PVLAN, nv=None, **extra):
    target = {"name": name, "sno": serial, "post": (policy, copy.deepcopy(nv if nv is not None else eth_nv(name))), "update": True}
    if kind:
        target["kind"] = kind
    target.update(extra)
    intf.pvlan_targets[(serial, name.lower())] = target
    return {"serialNumber": serial, "ifName": name}


def verify(intf, ctrl, sleep, items):
    """Run the REAL method once. Returns ("ok"|"fail", msg)."""
    with patch.object(basic.AnsibleModule, "exit_json", exit_json), patch.object(basic.AnsibleModule, "fail_json", fail_json), \
            patch.object(module, "dcnm_send", side_effect=ctrl), patch.object(module.time, "sleep", side_effect=sleep):
        try:
            intf.dcnm_intf_pvlan_verify_after_deploy(items)
        except AnsibleFailJson as exc:
            return "fail", exc.args[0]["msg"]
    return "ok", None


def eth_switch(serial, n, prefix="Ethernet1/"):
    return {"{0}{1}".format(prefix, i + 1): [PVLAN, eth_nv("{0}{1}".format(prefix, i + 1))] for i in range(n)}


def eth_setup(n, serials=(SN_A,)):
    ctrl = BatchController({sn: eth_switch(sn, n) for sn in serials})
    sleep = Sleep()
    intf = make_intf(ctrl, sleep)
    items = [add_target(intf, sn, name) for sn in serials for name in sorted(ctrl.ports[sn], key=lambda x: int(x.split("/")[1]))]
    return ctrl, sleep, intf, items


# ---------------------------------------------------------------- 1. counts on one switch (main acceptance case)
@pytest.mark.parametrize("n", [1, 10, 100])
def test_r2_batch_in_sync_ethernet_one_switch_reads_one_summary_and_one_bulk(n):
    ctrl, sleep, intf, items = eth_setup(n)
    status, msg = verify(intf, ctrl, sleep, items)
    print("R2-BATCH-COUNT eth n=%d summary=%d bulk=%d individual=%d sleep=%d" % (
        n, ctrl.count("summary"), ctrl.count("bulk"), ctrl.count("individual"), len(sleep.calls)))
    assert status == "ok", msg
    assert (ctrl.count("summary"), ctrl.count("bulk"), ctrl.count("individual"), sleep.calls) == (1, 1, 0, [])
    assert ctrl.writes() == []


@pytest.mark.parametrize("n", [1, 10, 100])
def test_r2_batch_every_target_is_still_judged_a_drift_on_the_last_one_fails(n):
    """The count reduction does not skip targets: a readback difference on the LAST target of the switch is still reported."""
    ctrl, sleep, intf, items = eth_setup(n)
    last = items[-1]["ifName"]
    ctrl.ports[SN_A][last][1]["PVLAN_NATIVE_VLAN"] = "2302"
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and msg == "Interface {0} on {1}: post-deploy intent readback differs in PVLAN_NATIVE_VLAN.".format(last, SN_A)
    assert (ctrl.count("summary"), ctrl.count("bulk")) == (1, 1)


def test_r2_batch_port_channels_on_one_switch_share_the_reads():
    ports = {"Port-channel{0}".format(500 + i): [PO_POLICY, po_nv("Port-channel{0}".format(500 + i), "Ethernet1/{0}".format(10 + i))]
             for i in range(10)}
    ctrl, sleep = BatchController({SN_A: ports}), Sleep()
    intf = make_intf(ctrl, sleep)
    items = [add_target(intf, SN_A, name, kind="po", policy=PO_POLICY, nv=ports[name][1]) for name in sorted(ports)]
    status, msg = verify(intf, ctrl, sleep, items)
    print("R2-BATCH-COUNT po n=10 summary=%d bulk=%d" % (ctrl.count("summary"), ctrl.count("bulk")))
    assert status == "ok", msg
    assert (ctrl.count("summary"), ctrl.count("bulk"), ctrl.count("individual")) == (1, 1, 0)


def test_r2_batch_a_port_channel_difference_is_still_reported():
    ports = {"Port-channel500": [PO_POLICY, po_nv("Port-channel500", "Ethernet1/10")], "Port-channel501": [PO_POLICY, po_nv("Port-channel501", "Ethernet1/11")]}
    ctrl, sleep = BatchController(copy.deepcopy({SN_A: ports})), Sleep()
    intf = make_intf(ctrl, sleep)
    items = [add_target(intf, SN_A, name, kind="po", policy=PO_POLICY, nv=ports[name][1]) for name in sorted(ports)]
    ctrl.ports[SN_A]["Port-channel501"][1]["PORT_DUPLEX_MODE"] = "full"
    ctrl.ports[SN_A]["Port-channel501"][1]["MEMBER_INTERFACES"] = "Ethernet1/12"
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail"
    assert msg == "Interface Port-channel501 on {0}: post-deploy intent readback differs in PORT_DUPLEX_MODE, MEMBER_INTERFACES.".format(SN_A)


def test_r2_batch_a_target_listed_twice_is_read_once_and_judged_each_time():
    ctrl, sleep, intf, items = eth_setup(3)
    ctrl.ports[SN_A]["Ethernet1/2"][1]["PVLAN_MODE"] = "host"
    status, msg = verify(intf, ctrl, sleep, items + items[1:2])
    assert status == "fail" and msg.startswith("Interface Ethernet1/2 on {0}: post-deploy intent readback differs in PVLAN_MODE".format(SN_A))
    assert (ctrl.count("summary"), ctrl.count("bulk")) == (1, 1)


# ---------------------------------------------------------------- 2. two switches, same interface names
def test_r2_batch_two_switches_read_once_each_and_keep_their_own_identity():
    ctrl, sleep, intf, items = eth_setup(10, serials=(SN_A, SN_B))
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "ok", msg
    assert [(sn, ctrl.count("summary", sn), ctrl.count("bulk", sn)) for sn in (SN_A, SN_B)] == [(SN_A, 1, 1), (SN_B, 1, 1)]


def test_r2_batch_homonymous_interface_drift_on_the_second_switch_is_not_masked_by_the_first():
    ctrl, sleep, intf, items = eth_setup(3, serials=(SN_A, SN_B))
    ctrl.ports[SN_B]["Ethernet1/2"][1]["PVLAN_ALLOWED_VLANS"] = "2301,2302"
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and msg == "Interface Ethernet1/2 on {0}: post-deploy intent readback differs in PVLAN_ALLOWED_VLANS.".format(SN_B)


def test_r2_batch_homonymous_interface_not_converged_on_one_switch_only():
    ctrl, sleep, intf, items = eth_setup(2, serials=(SN_A, SN_B))
    ctrl.status[(SN_B, "Ethernet1/1")] = ["Out-of-Sync"] * 6
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and msg.startswith("Interface Ethernet1/1 on {0} was deployed but did not reach In-Sync (last status Out-of-Sync).".format(SN_B))
    # SN_A converged in round 1 and is not read again; SN_B is read in each of the 6 rounds; 5 bounded waits in total.
    assert (ctrl.count("summary", SN_A), ctrl.count("summary", SN_B), sleep.calls) == (1, 6, [5] * 5)


# ---------------------------------------------------------------- 3. convergence rounds
def test_r2_batch_one_slow_target_others_in_sync_reads_the_switch_once_per_round():
    ctrl, sleep, intf, items = eth_setup(10)
    ctrl.status[(SN_A, "Ethernet1/7")] = ["Out-of-Sync", "Pending"]
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "ok", msg
    assert (ctrl.count("summary"), ctrl.count("bulk"), sleep.calls) == (3, 1, [5, 5])
    bulk_at = [i for i, c in enumerate(ctrl.calls) if ctrl.kind(c[1]) == "bulk"]
    summary_at = [i for i, c in enumerate(ctrl.calls) if ctrl.kind(c[1]) == "summary"]
    assert bulk_at[0] > summary_at[-1], "the readback is read only after the switch converged"


def test_r2_batch_late_convergence_of_every_target():
    ctrl, sleep, intf, items = eth_setup(5)
    for name in ctrl.ports[SN_A]:
        ctrl.status[(SN_A, name)] = ["Out-of-Sync"] * 4
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "ok", msg
    assert (ctrl.count("summary"), ctrl.count("bulk"), sleep.calls) == (5, 1, [5] * 4)


def test_r2_batch_exhausted_rounds_fail_with_the_last_status_and_the_same_bounds():
    ctrl, sleep, intf, items = eth_setup(4)
    ctrl.status[(SN_A, "Ethernet1/3")] = ["Out-of-Sync"] * 10
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail"
    assert msg == ("Interface Ethernet1/3 on {0} was deployed but did not reach In-Sync (last status Out-of-Sync). "
                   "No further deployment was sent.".format(SN_A))
    assert (ctrl.count("summary"), sleep.calls) == (6, [5] * 5)
    assert ctrl.writes() == []


def test_r2_batch_targets_before_a_non_converged_one_are_still_read_back_first():
    """The verdicts are reported in item order: a drift on an EARLIER converged target wins over a later non-converged one."""
    ctrl, sleep, intf, items = eth_setup(3)
    ctrl.ports[SN_A]["Ethernet1/1"][1]["PVLAN_MODE"] = "host"
    ctrl.status[(SN_A, "Ethernet1/3")] = ["Out-of-Sync"] * 10
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and msg.startswith("Interface Ethernet1/1 on {0}: post-deploy intent readback differs in PVLAN_MODE".format(SN_A))


# ---------------------------------------------------------------- 4. read errors and unproven states
def test_r2_batch_a_failed_summary_round_is_not_convergence_and_is_retried_in_the_next_round():
    ctrl, sleep, intf, items = eth_setup(10)
    ctrl.failures[("summary", SN_A)] = [True, True, True]  # one whole bounded GET (3 attempts) fails
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "ok", msg
    assert (ctrl.count("summary"), ctrl.count("bulk"), sleep.calls.count(5)) == (4, 1, 1)


def test_r2_batch_summary_never_readable_fails_without_claiming_convergence():
    ctrl, sleep, intf, items = eth_setup(3)
    ctrl.failures[("summary", SN_A)] = [True] * 18
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and "did not reach In-Sync (last status None)" in msg
    assert (ctrl.count("summary"), ctrl.count("bulk"), sleep.calls.count(5)) == (18, 0, 5)


@pytest.mark.parametrize("shape", ["missing", "duplicate", "malformed"])
def test_r2_batch_incomplete_summary_answers_are_not_convergence(shape):
    ctrl, sleep, intf, items = eth_setup(3)
    hooks = {
        "missing": lambda e: [x for x in e if x["ifName"] != "Ethernet1/2"],
        "duplicate": lambda e: e + [x for x in e if x["ifName"] == "Ethernet1/2"],
        "malformed": lambda e: [dict(x, complianceStatus=None) if x["ifName"] == "Ethernet1/2" else x for x in e],
    }
    ctrl.summary_hook[SN_A] = hooks[shape]
    status, msg = verify(intf, ctrl, sleep, items)
    # missing / duplicate: only that target is unproven. malformed: the reader rejects the WHOLE answer of the switch (an entry without a
    # compliance status), so no target of that switch is proven and the first one in item order is reported.
    first = "Ethernet1/1" if shape == "malformed" else "Ethernet1/2"
    assert status == "fail" and msg.startswith("Interface {0} on {1} was deployed but did not reach In-Sync".format(first, SN_A))
    assert (ctrl.count("summary"), ctrl.count("bulk"), sleep.calls.count(5)) == (6, 0 if shape == "malformed" else 1, 5)


def test_r2_batch_failed_bulk_falls_back_to_the_individual_read_of_each_target():
    ctrl, sleep, intf, items = eth_setup(3)
    ctrl.failures[("bulk", SN_A)] = [True, True, True]
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "ok", msg
    assert (ctrl.count("summary"), ctrl.count("bulk"), ctrl.count("individual")) == (1, 3, 3)


def test_r2_batch_unreadable_detail_is_never_a_pass():
    ctrl, sleep, intf, items = eth_setup(3)
    ctrl.failures[("bulk", SN_A)] = [True] * 3
    ctrl.failures[("individual", SN_A)] = [True] * 30
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and msg == "Interface Ethernet1/1 on {0}: the post-deploy readback does not hold policy {1}.".format(SN_A, PVLAN)


def test_r2_batch_wrong_policy_despite_in_sync_fails():
    ctrl, sleep, intf, items = eth_setup(3)
    ctrl.ports[SN_A]["Ethernet1/2"][0] = "int_trunk_host"
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and msg == "Interface Ethernet1/2 on {0}: the post-deploy readback does not hold policy {1}.".format(SN_A, PVLAN)


def test_r2_batch_target_absent_from_the_bulk_answer_fails():
    ctrl, sleep, intf, items = eth_setup(3)
    status_q = ctrl.ports[SN_A].pop("Ethernet1/3")
    ctrl.summary_hook[SN_A] = lambda e: e + [dict(e[0], ifName="Ethernet1/3", underlayPolicies=[{"templateName": status_q[0]}])]
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and msg == "Interface Ethernet1/3 on {0}: the post-deploy readback does not hold policy {1}.".format(SN_A, PVLAN)


# ---------------------------------------------------------------- 5. freshness across invocations
def test_r2_batch_second_call_reads_fresh_and_sees_a_new_difference():
    ctrl, sleep, intf, items = eth_setup(10)
    assert verify(intf, ctrl, sleep, items) == ("ok", None)
    ctrl.ports[SN_A]["Ethernet1/4"][1]["MAPPING_LIST"] = ""
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and "Ethernet1/4" in msg and "MAPPING_LIST" in msg
    assert (ctrl.count("summary"), ctrl.count("bulk")) == (2, 2), "no state of the first verification is reused"


def test_r2_batch_second_call_does_not_reuse_an_earlier_convergence():
    ctrl, sleep, intf, items = eth_setup(2)
    assert verify(intf, ctrl, sleep, items) == ("ok", None)
    ctrl.status[(SN_A, "Ethernet1/2")] = ["Out-of-Sync"] * 10
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and "Ethernet1/2" in msg and "did not reach In-Sync" in msg


def test_r2_batch_a_pre_deploy_cache_is_not_used_as_the_readback():
    ctrl, sleep, intf, items = eth_setup(2)
    with patch.object(module, "dcnm_send", side_effect=ctrl):
        intf.dcnm_intf_bulk_fetch_intf_info(SN_A)  # the pre-deploy authority read
    before = ctrl.count("bulk")
    ctrl.ports[SN_A]["Ethernet1/1"][1]["PVLAN_NATIVE_VLAN"] = "2399"  # what the controller holds after the deploy
    status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and "Ethernet1/1" in msg and "PVLAN_NATIVE_VLAN" in msg
    assert ctrl.count("bulk") == before + 1


# ---------------------------------------------------------------- 6. vPC route and released members (spies on their own verifiers)
class Spy(object):
    def __init__(self, ctrl, name):
        self.ctrl, self.name, self.calls = ctrl, name, []

    def __enter__(self):
        spy = self

        def wrapped(obj, target, *args, **kwargs):
            spy.calls.append((target["name"], len(spy.ctrl.calls)))

        self.original = getattr(module.DcnmIntf, self.name)
        setattr(module.DcnmIntf, self.name, wrapped)
        return self

    def __exit__(self, *exc):
        setattr(module.DcnmIntf, self.name, self.original)


def test_r2_batch_mixed_vpc_and_ethernet_keeps_the_vpc_verifier_once_and_in_place():
    ctrl, sleep, intf, items = eth_setup(4)
    vpc_item = add_target(intf, SN_A + "~" + SN_B, "vPC522", kind="vpc", policy="int_vpc_pvlan_host", nv={})
    mixed = items[:2] + [vpc_item] + items[2:]
    with Spy(ctrl, "dcnm_intf_pvlan_vpc_verify") as spy:
        status, msg = verify(intf, ctrl, sleep, mixed)
    assert status == "ok", msg
    assert [c[0] for c in spy.calls] == ["vPC522"]
    assert (ctrl.count("summary"), ctrl.count("bulk")) == (1, 1), "the vPC target adds no non-vPC read and is not batched"


def test_r2_batch_vpc_first_runs_before_any_non_vpc_read():
    ctrl, sleep, intf, items = eth_setup(2)
    vpc_item = add_target(intf, SN_A + "~" + SN_B, "vPC522", kind="vpc", policy="int_vpc_pvlan_host", nv={})
    with Spy(ctrl, "dcnm_intf_pvlan_vpc_verify") as spy:
        status, msg = verify(intf, ctrl, sleep, [vpc_item] + items)
    assert status == "ok", msg
    assert spy.calls == [("vPC522", 0)], "the vPC verifier ran before any request of the batch"
    assert (ctrl.count("summary"), ctrl.count("bulk")) == (1, 1)


def test_r2_batch_a_vpc_verifier_that_refreshes_the_shared_cache_does_not_change_the_ethernet_verdicts():
    """A vPC verifier between two Ethernet targets refreshes the bulk cache of the shared serial; the Ethernet verdict uses the
    post-convergence read of the batch, and a drift seen there is still reported."""
    ctrl, sleep, intf, items = eth_setup(3)
    ctrl.ports[SN_A]["Ethernet1/3"][1]["PVLAN_NATIVE_VLAN"] = "2350"
    vpc_item = add_target(intf, SN_A + "~" + SN_B, "vPC522", kind="vpc", policy="int_vpc_pvlan_host", nv={})

    def vpc_reads(obj, target):
        obj.dcnm_intf_bulk_fetch_intf_info(SN_A, refresh=True)

    with patch.object(module.DcnmIntf, "dcnm_intf_pvlan_vpc_verify", vpc_reads):
        status, msg = verify(intf, ctrl, sleep, items[:1] + [vpc_item] + items[1:])
    assert status == "fail" and msg.startswith("Interface Ethernet1/3 on {0}: post-deploy intent readback differs in PVLAN_NATIVE_VLAN".format(SN_A))
    assert ctrl.count("bulk") == 2, "one batch read + the vPC verifier's own read, counted separately"


def test_r2_batch_released_members_are_verified_per_port_channel_and_counted_apart():
    ports = {"Port-channel500": [PO_POLICY, po_nv("Port-channel500", "Ethernet1/10")], "Port-channel501": [PO_POLICY, po_nv("Port-channel501", "Ethernet1/11")]}
    ctrl, sleep = BatchController({SN_A: ports}), Sleep()
    intf = make_intf(ctrl, sleep)
    items = [add_target(intf, SN_A, name, kind="po", policy=PO_POLICY, nv=ports[name][1],
                        removed=[{"name": "Ethernet1/2%d" % i, "post": ("int_trunk_host", {})}]) for i, name in enumerate(sorted(ports))]
    with Spy(ctrl, "dcnm_intf_pvlan_po_verify_removed") as spy:
        status, msg = verify(intf, ctrl, sleep, items)
    assert status == "ok", msg
    assert [c[0] for c in spy.calls] == ["Port-channel500", "Port-channel501"]
    assert (ctrl.count("summary"), ctrl.count("bulk")) == (1, 1)


def test_r2_batch_released_members_are_not_verified_when_the_port_channel_readback_differs():
    ports = {"Port-channel500": [PO_POLICY, po_nv("Port-channel500", "Ethernet1/10")]}
    ctrl, sleep = BatchController(copy.deepcopy({SN_A: ports})), Sleep()
    intf = make_intf(ctrl, sleep)
    items = [add_target(intf, SN_A, "Port-channel500", kind="po", policy=PO_POLICY, nv=ports["Port-channel500"][1],
                        removed=[{"name": "Ethernet1/20", "post": ("int_trunk_host", {})}])]
    ctrl.ports[SN_A]["Port-channel500"][1]["ADMIN_STATE"] = "true"
    with Spy(ctrl, "dcnm_intf_pvlan_po_verify_removed") as spy:
        status, msg = verify(intf, ctrl, sleep, items)
    assert status == "fail" and "ADMIN_STATE" in msg and spy.calls == []


def test_r2_batch_non_pvlan_policy_targets_are_converged_and_policy_checked_only():
    """A release target (post policy other than int_pvlan_host) keeps its existing check: convergence plus policy, no PVLAN lists."""
    ctrl, sleep, intf, items = eth_setup(2)
    ctrl.ports[SN_A]["Ethernet1/2"] = ["int_trunk_host", {"MODE": "trunk"}]
    intf.pvlan_targets[(SN_A, "ethernet1/2")]["post"] = ("int_trunk_host", {"MODE": "trunk"})
    assert verify(intf, ctrl, sleep, items) == ("ok", None)
    assert (ctrl.count("summary"), ctrl.count("bulk")) == (1, 1)


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_delete_verify_batch.py
# The post-deploy verification of a PVLAN vPC DELETION reads ONE summary per peer serial and round (2 GETs per pair and
# round), whatever the number of vPCs or members, and judges every vPC of the pair on those answers.
#
# The intent, the release contract and the policy residue are proven FRESH BEFORE the deploy (the release proof and phase C of
# dcnm_intf_pvlan_vpc_release_members); after the deploy the module reads only what the deploy changed: the listings and the In-Sync
# status of each peer. The checks that used to run after the deploy are exercised here at the phase that now owns them (injected when
# the controller releases the members), and the contract change -- what is no longer re-read after the deploy -- is asserted
# explicitly. Same controller double and entry point as test_pvlan_vpc_batch (MultiVpc, the REAL main()). Values are
# SYNTHETIC. NOT LIVE TESTED by this file.
# ====================================================================================================
vpc_delete_verify_module = B.module
PA, PB = B.PA, B.PB


def deleted_setup(n, npairs=1, members=1):
    """N vPCs created and deployed, then the controller double moved to a new invocation with recording reset."""
    ctrl, config = B.created(n, npairs, members)
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.sleep_log[:] = []
    return ctrl, config


def delete_all(ctrl, config):
    items = []
    for c in config:
        index = next(i for i, pair in enumerate(B.PAIRS) if B.IPS[pair[0]] in c["switch"])
        items.append(ctrl.del_item(int(c["name"][3:]), index))
    return B.run(ctrl, items, state="deleted")


@pytest.mark.parametrize("members", [1, 2])
@pytest.mark.parametrize("n", [1, 2, 5, 10])
def test_deletion_reads_do_not_grow_with_the_number_of_vpcs(n, members):
    ctrl, config = deleted_setup(n, members=members)
    status, result = delete_all(ctrl, config)
    assert status == "exit" and result["changed"] is True, result.get("msg")
    # one round: ONE summary per peer serial = 2, whatever N and members per peer (previously 7: pair bulk, peer bulks and policy lists)
    assert B.post_kinds(ctrl) == {"summary": 2}
    assert B.post_gets(ctrl) == 2 and ctrl.sleep_log == []
    assert sorted(result["pvlan_verification"]) == sorted(c["name"].replace("vpc", "vPC") for c in config)
    assert all(v["state"] == "verified" and v["parent"] == "not listed" and set(v["peers"].values()) == {"verified"}
               for v in result["pvlan_verification"].values())


def test_two_pairs_cost_one_round_each_not_one_per_vpc():
    ctrl, config = deleted_setup(6, npairs=2)
    status, result = delete_all(ctrl, config)
    assert status == "exit", result.get("msg")
    assert B.post_kinds(ctrl) == {"summary": 4}


def test_a_vpc_whose_member_is_not_in_sync_fails_alone_and_the_others_are_still_reported():
    ctrl, config = deleted_setup(3)
    ctrl.ready_round[(V.SN2, "Ethernet2/11")] = None
    status, result = delete_all(ctrl, config)
    assert status == "fail", "a member that never reaches In-Sync cannot be reported as released"
    assert result["msg"].startswith("vPC vPC11 was deleted but its release could not be verified on every peer")
    assert "peer 2 (%s)" % V.SN2 in result["msg"] and "Ethernet2/11 is not In-Sync" in result["msg"]
    assert "vPC10" not in result["msg"] and "vPC12" not in result["msg"]
    states = dict((k, v["state"]) for k, v in result["pvlan_verification"].items())
    assert states == {"vPC10": "verified", "vPC11": "failed", "vPC12": "verified"}
    # the pair is read every round (2 GETs) until the budget of 6 rounds with 5 waits is spent: per pair, not per vPC
    assert (B.post_gets(ctrl), len(ctrl.sleep_log)) == (6 * 2, 5)


def test_two_failing_vpcs_are_both_named():
    ctrl, config = deleted_setup(3)
    ctrl.ready_round[(V.SN2, "Ethernet2/10")] = None
    ctrl.ready_round[(V.SN1, "Ethernet1/12")] = None
    status, result = delete_all(ctrl, config)
    assert status == "fail"
    assert "vPC vPC10 was deleted" in result["msg"] and "vPC vPC12 was deleted" in result["msg"] and "vPC vPC11 was deleted" not in result["msg"]
    assert dict((k, v["state"]) for k, v in result["pvlan_verification"].items()) == {"vPC10": "failed", "vPC11": "verified", "vPC12": "failed"}


def test_a_late_convergence_costs_a_round_per_pair_not_per_vpc():
    ctrl, config = deleted_setup(10)
    for k in range(10, 20):
        ctrl.ready_round[(V.SN1, "Ethernet1/%d" % k)] = 1
    status, result = delete_all(ctrl, config)
    assert status == "exit", result.get("msg")
    assert (B.post_gets(ctrl), len(ctrl.sleep_log)) == (2 * 2, 1)


@pytest.mark.parametrize("serial", [V.SN1, V.SN2])
def test_an_unreadable_peer_fails_every_vpc_of_the_pair_and_is_never_taken_for_absence(serial):
    ctrl, config = deleted_setup(3)
    ctrl.post_fail[("summary", serial)] = 10 ** 6
    status, result = delete_all(ctrl, config)
    assert status == "fail" and "the interface summary of %s could not be read authoritatively" % serial in result["msg"], result.get("msg")
    assert all(v["state"] == "failed" and v["parent"] == "unreadable" for v in result["pvlan_verification"].values())


@pytest.mark.parametrize("kind", ["bulk", "policies"])
def test_the_intent_and_policy_reads_are_not_repeated_after_the_deploy(kind):
    """Contract change: these were read after the deploy (fail-closed re-confirmations); a failure there can no longer fail the deletion."""
    ctrl, config = deleted_setup(3)
    for serial in B.PAIRS[0]:
        ctrl.post_fail[(kind, serial)] = 10 ** 6
    status, result = delete_all(ctrl, config)
    assert status == "exit" and all(v["state"] == "verified" for v in result["pvlan_verification"].values()), result.get("msg")
    assert B.post_kinds(ctrl) == {"summary": 2}


def test_one_transient_summary_failure_is_a_transport_retry_not_a_new_round():
    ctrl, config = deleted_setup(2)
    ctrl.post_fail[("summary", V.SN2)] = 1
    status, result = delete_all(ctrl, config)
    assert status == "exit", result.get("msg")
    # the reader's own bounded transport retry (3 attempts, 1 s apart): +1 GET and +1 wait, still one verification round
    assert (B.post_gets(ctrl), len(ctrl.sleep_log)) == (3, 1) and ctrl.sleep_log == [1]


@pytest.mark.parametrize("label, inject, needle", [
    ("child still listed", lambda c, s: c.post_extra.setdefault(s, []).append(c._summary_entry(s, "port-channel11", {"policy": V.VPC_PO}, "In-Sync")),
     "the interface summary still lists port-channel11"),
    ("member missing from the summary", lambda c, s: c.post_drop.setdefault(s, set()).add("Ethernet2/11" if s == V.SN2 else "Ethernet1/11"),
     "is not In-Sync in the interface summary"),
    ("member duplicated in the summary", lambda c, s: c.post_dup.setdefault(s, set()).add("Ethernet2/11" if s == V.SN2 else "Ethernet1/11"),
     "is not In-Sync in the interface summary"),
])
def test_a_partial_release_of_one_peer_fails_that_vpc_only(label, inject, needle):
    ctrl, config = deleted_setup(3)
    inject(ctrl, V.SN2)
    status, result = delete_all(ctrl, config)
    assert status == "fail", label
    assert result["msg"].startswith("vPC vPC11 was deleted but its release could not be verified on every peer"), (label, result["msg"][:200])
    assert needle in result["msg"] and "vPC10" not in result["msg"] and "vPC12" not in result["msg"], label
    assert result["pvlan_verification"]["vPC10"]["state"] == "verified" and result["pvlan_verification"]["vPC12"]["state"] == "verified"
    assert "peer 2 (%s)" % V.SN2 in result["msg"] and "peer 1" not in result["msg"], "the clean peer is not blamed"


def test_a_parent_back_in_the_intent_after_the_deploy_is_not_read_again():
    """Contract change: the parent's intent is not read after the deploy (the pair bulk used to re-confirm it). The deletion of the parent is
    proven by the confirmed mark-delete (or, for a saved deletion, the controller's marked-for-deletion listing); after the deploy the
    summaries prove it is no longer listed. A re-creation by another party after the deploy is outside the module's verification."""
    ctrl, config = deleted_setup(2)
    real = vpc_delete_verify_module.DcnmIntf.dcnm_intf_get_intf_info

    def parent_back(self, name, sno, kind, *a, **k):
        if ctrl.deployed and kind == "INTERFACE_VPC" and name == "vPC11":
            return {"policy": V.VPC_HOST}
        return real(self, name, sno, kind, *a, **k)

    from unittest.mock import patch
    with patch.object(vpc_delete_verify_module.DcnmIntf, "dcnm_intf_get_intf_info", parent_back):
        status, result = delete_all(ctrl, config)
    assert status == "exit", result.get("msg")
    assert result["pvlan_verification"]["vPC11"]["parent"] == "not listed" and B.post_kinds(ctrl) == {"summary": 2}


def test_the_same_vpc_name_on_two_pairs_is_judged_per_pair():
    ctrl, config = B.same_name_on_two_pairs()
    assert B.run(ctrl, config)[0] == "exit"
    ctrl.next_invocation()
    ctrl.calls = []
    ctrl.sleep_log[:] = []
    ctrl.ready_round[(B.PAIRS[1][1], "Ethernet2/10")] = None  # pair B, peer 2 only
    status, result = B.run(ctrl, [ctrl.del_item(10, 0), ctrl.del_item(10, 1)], state="deleted")
    assert status == "fail"
    assert "peer 2 (%s)" % B.PAIRS[1][1] in result["msg"]
    assert not any(s in result["msg"] for s in B.PAIRS[0]), "pair A's serials never appear in pair B's failure"


def test_a_reversed_switch_order_keeps_the_controller_peer_identity():
    ctrl, config = deleted_setup(2)
    items = [ctrl.del_item(10), ctrl.del_item(11)]
    items[1]["switch"] = list(reversed(items[1]["switch"]))
    status, result = B.run(ctrl, items, state="deleted")
    assert status == "exit", result.get("msg")
    assert B.post_gets(ctrl) == 2 and all(v["state"] == "verified" for v in result["pvlan_verification"].values())


# ============================================================== review F-1 / F-3: each remaining check has a discriminating test
class _PostDeploy(B.MultiVpc):
    """MultiVpc + post-deploy SUMMARY changes the harness does not offer: the member's listed policy (`post_policy`, (serial, ifName) ->
    template) and a compliance status from a given verification round on (`late_status`, (serial, ifName) -> (rounds waited, status));
    and a live policy added when the controller marks a vPC deleted (`marked_policy`, vPC name -> (serial, policy entry))."""

    def __init__(self, *a, **k):
        super(_PostDeploy, self).__init__(*a, **k)
        self.post_policy, self.late_status, self.marked_policy = {}, {}, {}

    def _peer_summary(self, serial):
        out = super(_PostDeploy, self)._peer_summary(serial)
        if not self.deployed:
            return out
        for e in out:
            key = (serial, e.get("ifName"))
            if key in self.post_policy and e.get("underlayPolicies"):
                e["underlayPolicies"][0]["templateName"] = self.post_policy[key]
            late = self.late_status.get(key)
            if late and len(self.sleep_log) >= late[0]:
                e["complianceStatus"] = late[1]
        return out

    def __call__(self, mod, method, path, data=None):
        if method == "DELETE" and path.endswith(V.MARKDELETE):
            name = json.loads(data)[0]["ifName"]
            if name in self.marked_policy:
                serial, policy = self.marked_policy[name]
                self.policies_extra[serial].append(policy)
        return super(_PostDeploy, self).__call__(mod, method, path, data)


def post_deploy_setup(n):
    ctrl, config = deleted_setup(n)
    ctrl.__class__ = _PostDeploy
    ctrl.post_policy, ctrl.late_status, ctrl.marked_policy = {}, {}, {}
    return ctrl, config


def marked_parent(pair_serial, name):
    """The MEASURED listing (NDFC 12.6.0.267) of a mark-deleted vPC parent in a peer's summary: markDeleted, Out-of-Sync, no underlay
    policy, while its intent (bulk detail) is already gone."""
    return {"ifName": name, "serialNo": pair_serial, "fabricName": "test_fabric", "ifType": "INTERFACE_VPC", "isPhysical": "False",
            "deletable": "True", "editAllowed": "True", "markDeleted": "True", "alias": "", "deleteReason": None,
            "complianceStatus": "Out-of-Sync", "underlayPolicies": [], "interfaces": [{"nvPairs": {}}]}


def test_a_parent_still_listed_after_the_deploy_fails_on_the_summary():
    """F-1: the partial-deploy detection belongs to the SUMMARY listing (the parent's intent is already empty after its mark-delete)."""
    ctrl, _config = deleted_setup(2)
    pair = B.PAIRS[0]
    for serial in pair:
        ctrl.post_extra[serial] = [marked_parent(pair[0] + "~" + pair[1], "vPC11")]
    status, result = B.run(ctrl, [ctrl.del_item(10), ctrl.del_item(11)], state="deleted")
    assert status == "fail" and "the interface summary still lists vPC11" in result["msg"], result.get("msg")
    assert result["pvlan_verification"]["vPC11"]["parent"] == "still listed"
    assert result["pvlan_verification"]["vPC11"]["state"] == "failed" and result["pvlan_verification"]["vPC10"]["state"] == "verified"
    assert result["pvlan_verification"]["vPC10"]["parent"] == "not listed"


def test_a_child_still_claimed_on_one_peer_is_refused_before_the_deploy():
    """F-3, moved: a child port-channel still live in one peer's intent carries its live policy; the fresh release proof refuses it
    before any deploy (it used to be found after the deploy with the peer's bulk read)."""
    ctrl, config = post_deploy_setup(3)
    ctrl.marked_policy["vPC11"] = (V.SN2, {"entityName": "port-channel11", "entityType": "INTERFACE", "templateName": V.VPC_PO, "source": "vPC11",
                                           "deleted": False, "policyId": "CHILD-LEFT", "serialNumber": V.SN2})
    status, result = delete_all(ctrl, config)
    assert status == "fail" and "PVLAN vPC vPC11" in result["msg"] and "(peer 2)" in result["msg"], result.get("msg")
    assert "live policies still reference the vPC or its child port-channel" in result["msg"] and "port-channel11" in result["msg"]
    assert ctrl.deploys() == [] and "pvlan_verification" not in result


def test_a_member_listed_with_another_policy_after_the_deploy_fails_that_vpc_only():
    """F-3: the summary entry of the released member reports a readable policy that is not the released one."""
    ctrl, config = post_deploy_setup(3)
    ctrl.post_policy[(V.SN1, "Ethernet1/11")] = "int_access_host"
    status, result = delete_all(ctrl, config)
    assert status == "fail" and result["msg"].startswith("vPC vPC11 was deleted but its release could not be verified"), result.get("msg")
    assert "lists the member Ethernet1/11 with int_access_host, not the released int_trunk_host" in result["msg"]
    assert "peer 1 (%s)" % V.SN1 in result["msg"] and "vPC10" not in result["msg"]


@pytest.mark.parametrize("value", [None, [], [{"templateName": "int_trunk_host"}, {"templateName": "int_access_host"}]])
def test_a_member_entry_without_a_readable_policy_is_not_judged_on_its_policy(value):
    """The summary reader requires the `underlayPolicies` key; its CONTENT is optional in the existing contract (pvlan_summary_policy:
    null or empty = no policy reported, several objects = unknown). Neither is a failure of the post-deploy proof, and no other read is made
    to recover the policy."""
    ctrl, config = deleted_setup(2)
    real = B.MultiVpc._peer_summary

    def no_policy(self, serial):
        out = real(self, serial)
        if self.deployed:
            for e in out:
                if e.get("ifName") == "Ethernet1/10":
                    e["underlayPolicies"] = value
        return out

    from unittest.mock import patch
    with patch.object(B.MultiVpc, "_peer_summary", no_policy):
        status, result = delete_all(ctrl, config)
    assert status == "exit" and result["pvlan_verification"]["vPC10"]["state"] == "verified", result.get("msg")
    assert B.post_kinds(ctrl) == {"summary": 2}


def test_a_member_changed_after_the_deploy_is_not_re_read():
    """Contract change: the member's intent (the peer bulk) is not read after the deploy; an administrative change made by another
    party after the pre-deploy proof is outside the module's verification (the external harness checks it)."""
    ctrl, config = deleted_setup(3)
    ctrl.post_mutate[(V.SN2, "Ethernet2/11")] = {"ADMIN_STATE": "true"}
    status, result = delete_all(ctrl, config)
    assert status == "exit" and all(v["state"] == "verified" for v in result["pvlan_verification"].values()), result.get("msg")


def test_a_vpc_verified_in_an_earlier_round_is_judged_again_until_its_pair_closes():
    """F-3: vPC10 is clean in round 1 while vPC11 is still converging; in round 2 vPC10's member is Out-of-Sync again. The pair is
    closed only when EVERY vPC is clean in the same round, so vPC10 is judged again and fails (a stale `verified` is never kept)."""
    ctrl, config = post_deploy_setup(2)
    ctrl.ready_round[(V.SN1, "Ethernet1/11")] = 1
    ctrl.late_status[(V.SN2, "Ethernet2/10")] = (1, "Out-of-Sync")
    status, result = delete_all(ctrl, config)
    assert status == "fail", "a vPC that regressed after an earlier clean round must not stay verified"
    assert "vPC vPC10 was deleted but its release could not be verified" in result["msg"], result["msg"][:300]
    assert result["pvlan_verification"]["vPC10"]["state"] == "failed" and result["pvlan_verification"]["vPC11"]["state"] == "verified"


# ====================================================================================================
# Formerly test_dcnm_intf_pvlan_vpc_po_verifier.py
# The Po deletion verifier (verified=False, failure after the reads run out, members not empty) is adopted with a
# `kind == "po"` filter. These tests show the two halves of that integration with the real main():
#
#   * a deleted vPC is verified by the vPC verifier and the Po verifier does not touch it (it issues no request for a vPC target);
#     a vPC target has no `members`, which the Po verifier REJECTS ("names no member"), so without the filter a valid vPC deletion
#     would fail (the fail-before is the mutant that removes the filter);
#   * a vPC whose release cannot be verified still fails (the vPC verifier, not the Po one).
# NOT LIVE TESTED; same synthetic harness as the other vPC tests.
# ====================================================================================================
class SpyPoVerifier(object):
    """Wraps the Po verifier: records how many requests it sent and how many deletion targets it could see."""

    def __init__(self, ctrl):
        self.ctrl, self.requests, self.targets = ctrl, None, None
        self.original = module.DcnmIntf.dcnm_intf_pvlan_po_verify_deleted

    def __enter__(self):
        spy = self

        def wrapped(obj):
            before = len(spy.ctrl.calls)
            spy.targets = [t for t in obj.dcnm_intf_pvlan_target_map().values() if t.get("deletes")]
            result = spy.original(obj)
            spy.requests = len(spy.ctrl.calls) - before
            return result

        module.DcnmIntf.dcnm_intf_pvlan_po_verify_deleted = wrapped
        return self

    def __exit__(self, *exc):
        module.DcnmIntf.dcnm_intf_pvlan_po_verify_deleted = self.original


def test_a_deleted_vpc_is_verified_by_the_vpc_verifier_and_the_po_verifier_sends_nothing_for_it():
    ctrl = created_ctrl()
    delete_previews(ctrl)
    with SpyPoVerifier(ctrl) as spy:
        status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "exit" and result["pvlan_verification"][VPC]["state"] == "verified", result.get("msg")
    assert [t.get("kind") for t in spy.targets] == ["vpc"], "the Po verifier is reached and SEES the vPC target"
    assert spy.requests == 0, "...and issues no request for it (kind == po filter)"
    assert result["pvlan_verification"][VPC]["peers"] == {SN1: "verified", SN2: "verified"}


def test_a_vpc_whose_release_cannot_be_verified_still_fails_through_the_vpc_verifier():
    ctrl = created_ctrl()
    ctrl.summary_failures = {SN1: [True] * 40, SN2: [True] * 40}  # The peers' summaries are the vPC verifier's only post-deploy reads
    delete_previews(ctrl)
    with SpyPoVerifier(ctrl) as spy:
        status, result = run_vpc(ctrl, [vpc_del_item()], state="deleted")
    assert status == "fail" and "release could not be verified on every peer" in result["msg"]
    assert result["pvlan_verification"][VPC]["state"] == "failed" and spy.requests == 0
