"""PR725 VPC-BATCH-GATE / VPC-READS: several PVLAN host vPCs of the SAME pair (and of two pairs) in ONE invocation, through the REAL main().

The controller double is the existing VpcController (test_dcnm_intf_pvlan_vpc_harness) for N vPCs over one or two pairs: vPC<k> with PCID k
and its own members on each peer, the harness stanzas with the id substituted, previews derived from the current state of each serial
(pending of every vPC created or deleted but not yet deployed), and post-deploy readiness / read-failure / drop / mutate injection.
Only the transport, inventory/version helpers and time.sleep (counted, never slept) are replaced. Values are SYNTHETIC.
NOT LIVE TESTED by this file."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import collections
import copy
import json
from unittest.mock import patch

import pytest

from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson, AnsibleFailJson, exit_json, fail_json
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from . import test_dcnm_intf_pvlan_vpc_harness as V
from .dcnm_module import set_module_args

PAIRS = ((V.SN1, V.SN2), ("FDO00000003", "FDO00000004"))
IPS = {V.SN1: V.IP1, V.SN2: V.IP2, "FDO00000003": "10.0.0.3", "FDO00000004": "10.0.0.4"}


def subst(lines, k):
    return [x.replace("port-channel10", "port-channel%d" % k).replace("vpc 10", "vpc %d" % k).replace("channel-group 10", "channel-group %d" % k)
            for x in lines]


class MultiVpc(V.VpcController):
    """VpcController for N vPCs over one or two pairs. The identity of a vPC is the controller's: its PAIR serial + its name, so the same
    name may exist on two pairs. `plan[(pair serial, name)] = (k, pair, members_peer1, members_peer2)`, `parents[(pair serial, name)]`."""

    def __init__(self, npairs=1):
        super(MultiVpc, self).__init__()
        self.pairs = PAIRS[:npairs]
        serials = [s for p in self.pairs for s in p]
        self.nodes = dict((s, {}) for s in serials)
        for attr in ("vpc_previews", "policies_extra", "summary_extra"):
            setattr(self, attr, dict((s, []) for s in serials))
        self.plan = {}
        self.deployed_vpcs, self.deleted_vpcs = set(), set()
        self.ready_round = {}     # (serial, ifName) -> waits after which the summary says In-Sync (None = never)
        self.sleep_log = []
        self.post_fail = {}       # (kind, serial) -> number of post-deploy GETs of that kind answered HTTP 500
        self.post_drop = {}       # serial -> {ifName} missing from post-deploy summaries
        self.post_dup = {}        # serial -> {ifName} listed twice in post-deploy summaries
        self.post_mutate = {}     # (serial, ifName) -> nvPairs applied to post-deploy detail reads
        self.post_mutate_parent = {}  # (pair serial, name) -> nvPairs applied to post-deploy reads of that parent
        self.extra_pending = {}   # serial -> pending lines appended to every preview of that serial

    def pair_of(self, serial):
        return [p for p in self.pairs if serial in p][0]

    @staticmethod
    def psn(pair):
        return pair[0] + "~" + pair[1]

    def add_vpc(self, k, pair_index=0, members=1, deploy=True, **profile):
        pair = self.pairs[pair_index]
        ports = (["Ethernet1/%d" % (k + 100 * i) for i in range(members)], ["Ethernet2/%d" % (k + 100 * i) for i in range(members)])
        for serial, plist in zip(pair, ports):
            for port in plist:
                nv = V.trunk_host_nv(port)
                nv["ADMIN_STATE"] = "false"
                self.nodes[serial][port] = {"policy": V.TRUNK, "nvPairs": nv}
        self.plan[(self.psn(pair), "vPC%d" % k)] = (k, pair, ports[0], ports[1])
        item = {"name": "vpc%d" % k, "type": "vpc", "switch": [IPS[pair[0]], IPS[pair[1]]], "deploy": deploy,
                "profile": {"mode": "pvlan", "pvlan_mode": "host", "peer1_members": ports[0], "peer2_members": ports[1], "peer1_pcid": k,
                            "peer2_pcid": k, "admin_state": False,
                            "pvlan_association": [{"primary_vlan": V.PRIMARY, "secondary_vlan": V.SECONDARY}]}}
        item["profile"].update(profile)
        return item

    def del_item(self, k, pair_index=0):
        pair = self.pairs[pair_index]
        return {"name": "vpc%d" % k, "type": "vpc", "switch": [IPS[pair[0]], IPS[pair[1]]], "deploy": True}

    def key(self, sno, name):
        """The plan key of the vPC `name` on the pair `sno`: exact pair serial, case-insensitive name; never another pair's entry."""
        found = [k for k in self.plan if k[0] == sno and k[1].lower() == str(name).lower()]
        assert len(found) == 1, (sno, name)
        return found[0]

    def _with_pair(self, key, fn):
        pair = self.plan[key][1]
        saved = (V.SN1, V.SN2, V.VPC, V.PAIR)
        V.SN1, V.SN2, V.VPC, V.PAIR = pair[0], pair[1], key[1], key[0]
        try:
            return fn()
        finally:
            V.SN1, V.SN2, V.VPC, V.PAIR = saved

    def _store_parent(self, intf, expand):
        key = self.key(intf["serialNumber"], intf["ifName"])
        nv = copy.deepcopy(intf["nvPairs"])
        nv.setdefault("INTF_NAME", intf["ifName"])
        self.parents[key] = {"policy": V.VPC_HOST, "nvPairs": nv}
        if expand:
            self._with_pair(key, lambda: V.VpcController._expand_children(self, nv))

    def _parent_nv(self, key, d):
        nv = copy.deepcopy(d["nvPairs"])
        if self.deployed:
            nv.update(self.post_mutate_parent.get(key, {}))
        return nv

    def _peer_summary(self, serial):
        out = []
        for name, d in sorted(self.nodes[serial].items()):
            status = self.compliance_by.get((serial, name), "In-Sync")
            if self.deployed and (serial, name) in self.ready_round:
                ready = self.ready_round[(serial, name)]
                status = "In-Sync" if (ready is not None and len(self.sleep_log) >= ready) else "Out-of-Sync"
            if self.deployed and name in self.post_drop.get(serial, set()):
                continue
            entry = self._summary_entry(serial, name, d, status)
            out.append(entry)
            if self.deployed and name in self.post_dup.get(serial, set()):
                out.append(copy.deepcopy(entry))
        out.extend(copy.deepcopy(self.summary_extra.get(serial, [])))
        for key in self.parents:
            if serial in self.plan[key][1]:
                e = self._summary_entry(serial, key[1], {"policy": V.VPC_HOST}, "In-Sync")
                e.update({"serialNo": key[0], "ifType": "INTERFACE_VPC", "isPhysical": "False"})
                out.append(e)
        return out

    def _peer_details(self, serial):
        out = []
        if "~" in serial:
            for key, d in self.parents.items():
                if serial == key[0]:
                    out.append({"policy": d["policy"], "interfaces": [{"serialNumber": serial, "ifName": key[1], "nvPairs": self._parent_nv(key, d)}]})
            return out
        for name, d in sorted(self.nodes[serial].items()):
            nv = copy.deepcopy(d["nvPairs"])
            if self.deployed:
                nv.update(self.post_mutate.get((serial, name), {}))
            out.append({"policy": d["policy"], "interfaces": [{"serialNumber": serial, "ifName": name, "nvPairs": nv}]})
        for key, d in self.parents.items():
            if serial in self.plan[key][1]:
                out.append({"policy": d["policy"], "interfaces": [{"serialNumber": key[0], "ifName": key[1], "nvPairs": self._parent_nv(key, d)}]})
        return out

    def _preview_for(self, serial):
        pending, running, expected = [], [], []
        for key, (k, pair, m1, m2) in sorted(self.plan.items(), key=lambda x: x[1][0]):
            if serial not in pair:
                continue
            ports = m1 if serial == pair[0] else m2
            # the child carries ITS pair's peer description (PEERn_PO_DESC of the parent stored under this pair identity)
            desc = (self.parents.get(key, {}).get("nvPairs") or {}).get("PEER%d_PO_DESC" % (1 if serial == pair[0] else 2)) or None
            po = subst(V.po_stanza(desc=desc), k)
            after = po + [x for p in ports for x in subst(V.member_after(p), k)]
            base = [x for p in ports for x in V.member_running_baseline(p)]
            if key in self.deleted_vpcs and key not in self.deployed_vpcs:
                withdrawn = [x for p in ports for x in subst(V.delete_preview(serial, p)["DATA"][0]["pendingConfig"][1:], k)]
                pending += ["no interface port-channel%d" % k] + withdrawn
                running += after
                expected += base
            elif key in self.parents and key not in self.deployed_vpcs:
                pending += po + [x for p in ports for x in subst(V.create_pending(p, desc=desc), k)[len(po):]]
                running += base
                expected += after
            elif key in self.parents:
                running += after
                expected += after
            else:
                running += base
                expected += base
        pending += self.extra_pending.get(serial, [])
        return V.preview(pending, serial=serial, running=running, expected=expected)

    def __call__(self, mod, method, path, data=None):
        if "vpcpair_serial_number" in path:
            self.calls.append((method, path, data))
            return V.ok({"vpc_pair_sn": self.psn(self.pair_of(path.split("serial_number=")[1].split("&")[0]))})
        if V.PREVIEW_MARK in path:
            self.calls.append((method, path, data))
            return self._preview_for(path.split("config-preview/")[1].split("?")[0])
        if method == "GET" and self.deployed:
            kind = kind_of(path)
            serial = serial_of(path)
            if self.post_fail.get((kind, serial), 0) > 0:
                self.calls.append((method, path, data))
                self.post_fail[(kind, serial)] -= 1
                return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
        if method == "POST" and path.endswith(V.GLOBAL_IF):
            # the parent is stored under its PAIR identity; the children of THAT pair are expanded as the harness predicts
            self.calls.append((method, path, data))
            resp = self.create_responses.pop(0) if self.create_responses else V.ok({})
            body = json.loads(data)
            if resp.get("RETURN_CODE") in (200, 207):
                for payload in body if isinstance(body, list) else [body]:
                    assert payload["policy"] == V.VPC_HOST, payload["policy"]
                    for intf in payload["interfaces"]:
                        self._store_parent(intf, self.children_on_save)
            return resp
        if method == "POST" and path.endswith(V.MODIFY):
            body = json.loads(data)
            if any(p_["policy"] == V.VPC_HOST for p_ in body):
                assert all(p_["policy"] == V.VPC_HOST for p_ in body) and not self.modify_responses
                self.calls.append((method, path, data))
                for payload in body:
                    for intf in payload["interfaces"]:
                        self._store_parent(intf, True)
                return {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [
                    {"reportItemType": "SUCCESS", "message": "Interface updated successfully", "entity": "%s~%s" % (i["serialNumber"], i["ifName"])}
                    for p_ in body for i in p_["interfaces"]]}
        if method == "DELETE" and path.endswith(V.MARKDELETE):
            items = json.loads(data)
            assert len(items) == 1, items  # the module marks one vPC per request
            key = self.key(items[0]["serialNumber"], items[0]["ifName"])
            self.deleted_vpcs.add(key)
            self.deployed_vpcs.discard(key)
            saved = self.parents
            self.parents = {key[1]: saved.pop(key)} if key in saved else {}
            try:
                return self._with_pair(key, lambda: super(MultiVpc, self).__call__(mod, method, path, data))
            finally:
                self.parents = saved
        if method == "POST" and path.endswith(V.DEPLOY):
            for d in json.loads(data):
                if "~" in str(d.get("serialNumber")):
                    self.deployed_vpcs.add(self.key(d["serialNumber"], d["ifName"]))
        return super(MultiVpc, self).__call__(mod, method, path, data)


def kind_of(path):
    if "config-preview" in path:
        return "preview"
    if "/rest/interface/detail?serialNumber=" in path:
        return "summary"
    if "/control/policies/switches/" in path:
        return "policies"
    if "/rest/interface?serialNumber=" in path:
        return "individual" if "&ifName=" in path else "bulk"
    if "vpcpair_serial_number" in path:
        return "vpcpair"
    return path.split("/rest/")[-1].split("?")[0] if "/rest/" in path else path


def serial_of(path):
    if "/control/policies/switches/" in path:
        return path.rsplit("/", 1)[1]
    if "config-preview/" in path:
        return path.split("config-preview/")[1].split("?")[0]
    for key in ("serialNumber=", "serial_number="):
        if key in path:
            return path.split(key)[1].split("&")[0]
    return None


def run(ctrl, config, state="merged"):
    inv = dict((IPS[sn], {"logicalName": "sw-%s" % sn[-1], "serialNumber": sn, "isVpcConfigured": "True", "vpcDomain": 10 + i // 2,
                          "switchRole": "leaf", "managable": "True"}) for i, sn in enumerate(sorted(ctrl.nodes)))
    args = {"state": state, "fabric": V.FABRIC, "config": config, "check_deploy": False}
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


def phase_counts(ctrl):
    """GET counts by phase (pre-write / before deploy / after the LAST deploy) and kind, from the recorded requests."""
    calls = ctrl.calls
    first_write = next((i for i, c in enumerate(calls) if c[0] != "GET"), len(calls))
    deploys = [i for i, c in enumerate(calls) if c[0] == "POST" and c[1].endswith(V.DEPLOY)]
    last = deploys[-1] if deploys else len(calls)
    out = collections.Counter()
    for i, (method, path, _d) in enumerate(calls):
        phase = "pre" if i < first_write else "post" if i > last else "mid"
        out["%s %s %s" % (phase, method, kind_of(path))] += 1
    return out


def post_gets(ctrl):
    return sum(v for k, v in phase_counts(ctrl).items() if k.startswith("post GET"))


def created(n, npairs=1, members=1):
    ctrl = MultiVpc(npairs)
    config = [ctrl.add_vpc(10 + i, i % npairs, members=members) for i in range(n)]
    return ctrl, config


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


def post_kinds(ctrl):
    return dict((k.split(" ", 2)[2], v) for k, v in phase_counts(ctrl).items() if k.startswith("post GET"))


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


# ------------------------------------------------------------------ IDENTITY: the same vPC name on two pairs (review of 80c37c8)
# The controller identifies a vPC by its PAIR serial + its name. vPC10 exists on both pairs, with the SAME member names on different serials
# and DIFFERENT expected values per pair (peer1 description), so a plan keyed by the name alone would judge one pair with the other's data.
PA, PB = PAIRS[0][0] + "~" + PAIRS[0][1], PAIRS[1][0] + "~" + PAIRS[1][1]


def same_name_on_two_pairs():
    ctrl = MultiVpc(2)
    config = [ctrl.add_vpc(10, 0, peer1_description="pair-a-p1"), ctrl.add_vpc(10, 1, peer1_description="pair-b-p1")]
    return ctrl, config


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
