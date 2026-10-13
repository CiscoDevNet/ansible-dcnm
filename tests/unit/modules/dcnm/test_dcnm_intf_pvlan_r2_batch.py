"""PR725-R2-BATCH: read planning of the PVLAN post-deploy verifier (dcnm_intf_pvlan_verify_after_deploy).

The REAL method runs on a REAL DcnmIntf; only the external boundary is replaced: dcnm_send by a serial-routed controller double that
records every request before answering it, and time.sleep by a counter. Counts are of the HTTP GETs the module itself sends through
its own readers (dcnm_intf_get_have_all_with_sno -> summary, dcnm_intf_bulk_fetch_intf_info -> bulk, dcnm_intf_get_intf_info ->
individual), not of calls to a stub. vPC targets and released members keep their own verifiers; here they are observed through spies
so that their position, number of calls and requests are asserted, while their behavior stays covered by the existing vPC/Po suites.
NOT LIVE TESTED: offline request counts only, no controller latency claim."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest
from unittest.mock import patch

from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import (
    AnsibleFailJson,
    exit_json,
    fail_json,
)
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .dcnm_module import set_module_args
from .test_dcnm_intf_pvlan_harness import FABRIC, NDFC, PVLAN, TRANSITIONS, ok

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
