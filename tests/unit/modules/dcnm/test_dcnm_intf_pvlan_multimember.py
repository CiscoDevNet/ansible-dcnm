"""Multiple physical PVLAN members: reuse existing transport harness and stanzas.

Offline module regressions, not new live-controller measurements. Membership
cardinality is varied; unrelated nvPair matrices deliberately are not repeated.
"""
import copy
import json

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from . import test_dcnm_intf_pvlan_vpc_harness as V
from . import test_dcnm_intf_pvlan_po_host as H
from .test_dcnm_intf_pvlan_po_g1 import PoLifecycleController

PORTS = {V.SN1: [V.M1, "Ethernet1/9", "Ethernet1/10"], V.SN2: [V.M2, "Ethernet1/11"]}


def vpc_baseline():
    ctrl = V.VpcController()
    for serial, ports in PORTS.items():
        for port in ports:
            nv = V.trunk_host_nv(port)
            nv["ADMIN_STATE"] = "false"
            ctrl.nodes[serial][port] = {"policy": V.TRUNK, "nvPairs": nv}
    return ctrl


def vpc_item(**kw):
    return V.vpc_item(peer1_members=PORTS[V.SN1], peer2_members=PORTS[V.SN2], **kw)


def combine_previews(serial, ports, factory, *args):
    """One switch preview, assembled from existing explicit per-port fixtures."""
    entries = [P.preview_entry(factory(serial, port, *args), serial) for port in ports]
    fields = {}
    for key in ("pendingConfig", "runningConfig", "expectedConfig"):
        lines = []
        for i, entry in enumerate(entries):
            current = None
            for line in entry[key]:
                if line.lower().strip().startswith("interface "):
                    current = line.lower().strip()[10:]
                if i and (current == "port-channel10" or line.lower().strip() == "no interface port-channel10"):
                    continue
                lines.append(line)
        fields[key] = lines
    return V.preview(fields["pendingConfig"], serial=serial, running=fields["runningConfig"], expected=fields["expectedConfig"])


def queue(ctrl, factory, *args):
    for serial, ports in PORTS.items():
        ctrl.vpc_previews[serial].append(combine_previews(serial, ports, factory, *args))


def seeded_vpc():
    ctrl = vpc_baseline().seed_vpc()
    nv = ctrl.parents[V.VPC]["nvPairs"]
    for n, serial in enumerate((V.SN1, V.SN2), 1):
        nv["PEER%d_MEMBER_INTERFACES" % n] = ",".join(PORTS[serial])
    ctrl._expand_children(nv)
    ctrl.next_invocation()
    return ctrl


@pytest.mark.parametrize("reverse", [False, True])
def test_vpc_create_full_lists_on_correct_peers_then_repeat_with_reordered_aliases(reverse):
    ctrl = vpc_baseline()
    queue(ctrl, V.create_preview)
    item = vpc_item()
    if reverse:
        item["switch"].reverse()
        item["profile"]["peer1_members"], item["profile"]["peer2_members"] = PORTS[V.SN2], PORTS[V.SN1]
    status, result = V.run_vpc(ctrl, [item])
    assert status == "exit", result.get("msg")
    assert len(ctrl.creates()) == 1 and len(ctrl.deploys()) == 1
    parent = ctrl.parents[V.VPC]["nvPairs"]
    assert parent["PEER1_MEMBER_INTERFACES"] == ",".join(PORTS[V.SN1])
    assert parent["PEER2_MEMBER_INTERFACES"] == ",".join(PORTS[V.SN2])
    assert len(ctrl.previews_asked()) == 2, "one fresh preview per switch, not per member"
    ctrl.next_invocation()
    ctrl.calls = []
    queue(ctrl, V.converged_preview)
    item = vpc_item()
    for peer in (1, 2):
        key = "peer%d_members" % peer
        item["profile"][key] = [p.replace("Ethernet", "e") for p in reversed(item["profile"][key])]
    status, result = V.run_vpc(ctrl, [item])
    assert status == "exit" and result["changed"] is False, result.get("msg")
    assert ctrl.writes() == []


def test_vpc_description_update_preserves_every_omitted_member():
    ctrl = seeded_vpc()
    queue(ctrl, V.converged_preview)
    queue(ctrl, V.description_preview, "", "multiple")
    item = vpc_item(peer1_description="multiple", peer2_description="multiple")
    del item["profile"]["peer1_members"], item["profile"]["peer2_members"]
    status, result = V.run_vpc(ctrl, [item])
    assert status == "exit", result.get("msg")
    assert len(ctrl.modifies()) == 1 and len(ctrl.deploys()) == 1
    for n, serial in enumerate((V.SN1, V.SN2), 1):
        assert ctrl.parents[V.VPC]["nvPairs"]["PEER%d_MEMBER_INTERFACES" % n] == ",".join(PORTS[serial])


@pytest.mark.parametrize("serial, port", [(V.SN1, PORTS[V.SN1][-1]), (V.SN2, PORTS[V.SN2][-1])])
def test_vpc_rejects_foreign_last_member_before_any_write(serial, port):
    ctrl = vpc_baseline()
    ctrl.nodes[serial][port]["policy"] = V.PO_MEMBER
    ctrl.nodes[serial][port]["nvPairs"]["PO_ID"] = "port-channel99"
    status, result = V.run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and ctrl.writes() == [], result.get("msg")
    assert port.lower() in result["msg"].lower()


def test_vpc_bad_middle_member_preview_prevents_deploy():
    ctrl = vpc_baseline()
    queue(ctrl, V.create_preview)
    entry = P.preview_entry(ctrl.vpc_previews[V.SN1][0], V.SN1)
    # Remove an entire required member from expectedConfig, retaining good last port.
    blocks = P.split_blocks(entry["expectedConfig"])[0]
    expected = []
    for name, lines in blocks.items():
        if name != PORTS[V.SN1][1].lower():
            expected += ["interface " + name] + lines
    ctrl.vpc_previews[V.SN1][0] = V.preview(entry["pendingConfig"], serial=V.SN1,
                                            running=entry["runningConfig"], expected=expected)
    status, result = V.run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and len(ctrl.creates()) == 1 and ctrl.deploys() == [], result.get("msg")


def test_vpc_readback_does_not_overwrite_a_wrong_middle_member_with_the_good_last_member():
    class WrongReadback(V.VpcController):
        def __call__(self, mod, method, path, data=None):
            result = super().__call__(mod, method, path, data)
            if method == "POST" and path.endswith(V.DEPLOY):
                self.nodes[V.SN1][PORTS[V.SN1][1]]["nvPairs"]["LACP_PORT_PRIO"] = "99"
            return result
    ctrl = vpc_baseline()
    ctrl.__class__ = WrongReadback
    queue(ctrl, V.create_preview)
    status, result = V.run_vpc(ctrl, [vpc_item()])
    assert status == "fail" and len(ctrl.deploys()) == 1, result.get("msg")
    assert "LACP_PORT_PRIO" in result["msg"], result.get("msg")


def test_vpc_delete_releases_and_verifies_all_five_members():
    ctrl = seeded_vpc()
    queue(ctrl, V.delete_preview)
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert status == "exit", result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.modifies()) == 5 and len(ctrl.deploys()) == 1
    identities = {(i["serialNumber"], i["ifName"]) for c in ctrl.modifies() for p in json.loads(c[2]) for i in p["interfaces"]}
    assert identities == {(s, p) for s, ports in PORTS.items() for p in ports}
    for serial, port in identities:
        assert ctrl.nodes[serial][port]["nvPairs"]["ADMIN_STATE"] == "false"
    verified = result["pvlan_verification"][V.VPC]
    assert verified["state"] == "verified" and len(verified["peers"]) == 5


def test_vpc_invalid_last_release_blocks_all_member_writes():
    class InvalidRelease(V.VpcController):
        def __call__(self, mod, method, path, data=None):
            result = super().__call__(mod, method, path, data)
            if method == "DELETE" and path.endswith(V.MARKDELETE):
                nv = self.nodes[V.SN2][PORTS[V.SN2][-1]]["nvPairs"]
                nv.update(ADMIN_STATE="false", ALLOWED_VLANS="all")
            return result
    ctrl = seeded_vpc()
    ctrl.__class__ = InvalidRelease
    status, result = V.run_vpc(ctrl, [V.vpc_del_item()], state="deleted")
    assert status == "fail" and len(ctrl.markdeletes()) == 1, result.get("msg")
    assert ctrl.modifies() == [] and ctrl.deploys() == []


@pytest.mark.parametrize("members", [["Ethernet1/7", "e1/7"], ["Ethernet1/7", "Ethernet1/8-10"], ["Ethernet1/7", 9]])
def test_member_validation_refuses_alias_duplicates_ranges_and_non_strings(members):
    assert P.po_not_implemented(H.po_item(members=members)["profile"])
    assert P.vpc_not_implemented(V.vpc_item(peer1_members=members)["profile"], V.VPC)


def po_seeded():
    ctrl = PoLifecycleController()
    # Parent fixture from the existing contract; explicit members with independent descriptors.
    nv = P.po_host_nvpairs(H.po_item(members=PORTS[V.SN1])["profile"], H.PO)
    ctrl.detail[H.PO] = {"policy": H.PO_HOST, "nvPairs": nv}
    ctrl.po_names.add(H.PO)
    for port in PORTS[V.SN1]:
        ctrl.detail[port] = {"policy": H.PO_MEMBER, "nvPairs": {
            "PO_ID": H.PO, "PC_MODE": "active", "PVLAN_MODE": "host", "CDP_ENABLE": "true",
            "lldpTransmit": "false", "lldpReceive": "false", "LACP_PORT_PRIO": "32768", "LACP_RATE": "normal",
            "DESC": "", "CONF": "", "ADMIN_STATE": "false", "INTF_NAME": port}}
    return ctrl


def test_regular_po_create_sends_all_members():
    ctrl = H.PoController()
    for port in PORTS[V.SN1]:
        ctrl.detail[port] = {"policy": H.TRUNK, "nvPairs": H.trunk_host_nv(port)}
    status, result = H.run(ctrl, [H.po_item(members=PORTS[V.SN1], deploy=False)])
    assert status == "exit", result.get("msg")
    assert ctrl.detail[H.PO]["nvPairs"]["MEMBER_INTERFACES"] == ",".join(PORTS[V.SN1])
    assert len(ctrl.creates()) == 1


def test_regular_po_repeat_keeps_controller_representation_of_all_members():
    ctrl = po_seeded()
    before = copy.deepcopy(ctrl.detail[H.PO]["nvPairs"])
    status, result = H.run(ctrl, [H.po_item(members=list(reversed(PORTS[V.SN1])), deploy=False)])
    assert status == "exit" and result["changed"] is False and ctrl.writes() == [], result.get("msg")
    assert ctrl.detail[H.PO]["nvPairs"] == before


def test_regular_po_delete_restores_every_member():
    ctrl = po_seeded()
    pv = P.preview_entry(combine_previews(H.SERIAL, PORTS[V.SN1], V.delete_preview), H.SERIAL)
    pv["runningConfig"] = [line for line in pv["runningConfig"] if line.strip() != "vpc 10"]
    ctrl.previews = [H.preview(pv["pendingConfig"], running=pv["runningConfig"], expected=pv["expectedConfig"])]
    status, result = H.run(ctrl, [{"name": H.PO_ITEM_NAME, "switch": [H.SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "exit", result.get("msg")
    assert len(ctrl.markdeletes()) == 1 and len(ctrl.deploys()) == 1
    assert {r["member"] for r in result["pvlan_po_release"]} == set(PORTS[V.SN1])
    assert all(ctrl.detail[p]["policy"] == H.TRUNK for p in PORTS[V.SN1])


def test_regular_po_unsafe_last_release_blocks_every_member_modify():
    class InvalidRelease(PoLifecycleController):
        def __call__(self, mod, method, path, data=None):
            result = super().__call__(mod, method, path, data)
            if method == "DELETE" and path.endswith(V.MARKDELETE):
                for port in PORTS[V.SN1]:
                    self.detail[port]["nvPairs"]["ADMIN_STATE"] = "true"
                self.detail[PORTS[V.SN1][-1]]["nvPairs"].update(ADMIN_STATE="false", ALLOWED_VLANS="all")
            return result
    ctrl = po_seeded()
    ctrl.__class__ = InvalidRelease
    status, result = H.run(ctrl, [{"name": H.PO_ITEM_NAME, "switch": [H.SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and len(ctrl.markdeletes()) == 1, result.get("msg")
    assert ctrl.bulk_bodies() == [] and ctrl.deploys() == []


def test_regular_po_partial_release_reports_previous_member_write_and_stops():
    class FailedSecondWrite(PoLifecycleController):
        def __call__(self, mod, method, path, data=None):
            if method == "POST" and path.endswith(V.MODIFY):
                member = json.loads(data)[0]["interfaces"][0]["ifName"]
                if member == sorted(PORTS[V.SN1], key=str.lower)[1]:
                    self.modify_responses.append({"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [
                        {"reportItemType": "ERROR", "message": "injected second member failure", "entity": H.SERIAL + "~" + member}]})
            result = super().__call__(mod, method, path, data)
            if method == "DELETE" and path.endswith(V.MARKDELETE):
                for port in PORTS[V.SN1]:
                    self.detail[port]["nvPairs"]["ADMIN_STATE"] = "true"
            return result
    ctrl = po_seeded()
    ctrl.__class__ = FailedSecondWrite
    status, result = H.run(ctrl, [{"name": H.PO_ITEM_NAME, "switch": [H.SWITCH_IP], "deploy": True}], state="deleted")
    assert status == "fail" and ctrl.deploys() == [], result.get("msg")
    assert len(ctrl.bulk_bodies()) == 2
    first = sorted(PORTS[V.SN1], key=str.lower)[0]
    assert "modify of %s ADMIN_STATE false (per-item SUCCESS)" % first in result["msg"]
    assert ctrl.detail[first]["nvPairs"]["ADMIN_STATE"] == "false"
