"""VPC-HOST-E1-OFFLINE: the minimal two-serial extension of the existing PVLAN harness.

NOT LIVE TESTED. Real main(); only the external boundary is mocked, through the EXISTING harness
(test_dcnm_intf_pvlan_harness.FakeController) plus the smallest subclass that teaches it a PAIR of switches: state per serial, the
vPC parent that appears on both peers, per-serial previews/policy lists and a vPC create/delete. No new framework or simulator.

E4 (VPC-HOST-E4-G6) labelling of the shapes taken from the regular Po campaign (fixtures/pvlan_po_h1_measured.json, NDFC 12.6.0.267):
  MEASURED for a REGULAR host Po, SIMULATED here for a vPC: the member joins through the pending COMMAND `channel-group N force mode M` while the
  controller's expected member and the device keep the PERSISTED `channel-group N mode M`; an existing member inherits its Po's association change with
  NO member pending; a deployed member leaves with the command form `no channel-group N force mode M`; the mark-delete answers 200/OK 'Interface deleted
  successfully' with ONE `value` item; the controller releases the member as int_trunk_host with ADMIN_STATE "true".
  Nothing of this has been observed for a vPC: it is the extrapolation L1 measures.

Three kinds of data, never mixed (the worklog's "contract of the source / synthetic fixture / future live measurement"):
  * contract of the source   -- what the captured templates and the existing module code say (cited in the tests);
  * SYNTHETIC fixture        -- every preview/summary/policy shape below is written BY HAND from those templates. The fake applies
                                 on a create/delete exactly what the templates are PREDICTED to do (children per peer, member flip,
                                 member release); that prediction is the hypothesis under test, not a controller measurement;
  * future live measurement  -- the first live case (L1) measures it. Nothing here certifies the controller.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json

from unittest.mock import patch

from ansible.module_utils import basic
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    exit_json,
    fail_json,
)
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .dcnm_module import set_module_args
from .test_dcnm_intf_pvlan_harness import (
    FABRIC,
    NDFC,
    PREVIEW_MARK,
    TRUNK,
    FakeController,
    ok,
    preview,
    trunk_host_nv,
)

SN1, SN2 = "FDO00000001", "FDO00000002"
IP1, IP2 = "10.0.0.1", "10.0.0.2"
PAIR = SN1 + "~" + SN2
VPC = "vPC10"
PO = "port-channel10"
M1, M2 = "Ethernet1/7", "Ethernet1/8"  # DIFFERENT ports per peer, so a crossed assignment is visible
VPC_HOST = "int_vpc_pvlan_host"
VPC_PO = "int_vpc_pvlan_po"
PO_MEMBER = "int_port_channel_pvlan_member"
GLOBAL_IF = "/rest/globalInterface"
DEPLOY = "/rest/globalInterface/deploy"
MODIFY = "/rest/interface/modify"
MARKDELETE = "/rest/interface/markdelete"
PRIMARY, SECONDARY = 2210, 2212

INVENTORY = dict(
    (ip, {"logicalName": "sw-%d" % (i + 1), "serialNumber": sn, "isVpcConfigured": "True", "vpcDomain": 10, "switchRole": "leaf", "managable": "True"})
    for i, (ip, sn) in enumerate(((IP1, SN1), (IP2, SN2)))
)


def pid(serial, name):
    return "POLICY-%s-%s" % (serial, name)


class VpcController(FakeController):
    """FakeController + a PAIR of switches. `nodes[serial][ifName]` holds the per-peer interfaces (Ethernet members, child Po),
    `parents[name]` the vPC parent (pair identity). Pending is NEVER computed: previews are queued per serial by each test."""

    def __init__(self):
        super(VpcController, self).__init__()
        self.nodes = {SN1: {}, SN2: {}}
        self.parents = {}
        self.vpc_previews = {SN1: [], SN2: []}
        self.policies_extra = {SN1: [], SN2: []}
        self.policy_failures = {}  # serial -> list consumed per policy-list read AFTER a deploy (True = HTTP 500)
        self.create_responses = []
        self.children_on_save = True  # [INF] the parent's add() writes the children when the intent is saved (HOST 590-600): L1 measures it
        self.release_on_delete = True  # [UNK] V6: the members return to int_trunk_host after the vPC is deleted
        self.release_admin_up = True  # MEASURED for a regular Po (HR), INFERRED for a vPC: the released member is int_trunk_host ADMIN_STATE "true"
        self.markdelete_responses = []  # consumed in order; default: the measured Po answer with the PAIR identity (INFERRED for a vPC)
        self.member_modify_fail = set()  # serials whose member modify answers an ERROR item
        self.children_marked_deleted = False  # MEASURED (L1-E4 live F): the deleted vPC's child Po stays listed as `interface_delete` until the deploy
        self.marked_source = None  # the `interface_delete` source; None = the parent vPC (MEASURED: `vpc10`, lower case); set to model a foreign owner
        self.parent_metadata = {"createVpc": "true"}  # MEASURED (L1-E4 live A1/A2): the controller adds `createVpc` "true" to the created parent
        self.list_parent_policy = False  # [UNK] V2: whether the parent policy is listed on a peer
        self.vpc_in_summary = True  # [UNK] V0: whether the vPC is an entry of the interface summary
        self.inherited_child = True  # the 'Inherited Commands' int_eth child of every member (HOST 755-780)
        self.summary_extra = {SN1: [], SN2: []}  # entries listed by the interface summary of a peer and by nothing else
        self.compliance_by = {}  # (serial, ifName) -> status
        self.markdeleted = False

    # ---- seeding (explicit state, never produced by the code under test)
    def seed_baseline(self):
        for serial, port in ((SN1, M1), (SN2, M2)):
            nv = trunk_host_nv(port)
            nv["ADMIN_STATE"] = "false"
            self.nodes[serial][port] = {"policy": TRUNK, "nvPairs": nv}
        return self

    def seed_vpc(self, association=((PRIMARY, SECONDARY),), descs=("", ""), admin="false"):
        """A coherent, created vPC (SYNTHETIC): parent + one child Po and one member per peer."""
        wire = json.dumps({"ASSOCIATION_LIST": [{"P_VLAN": str(p), "S_VLAN": str(s)} for p, s in association]}, separators=(",", ":"))
        parent = {
            "PC_MODE": "active",
            "BPDUGUARD_ENABLED": "true",
            "PORTTYPE_FAST_ENABLED": "true",
            "spanningTreePortType": "no",
            "MTU": "jumbo",
            "SPEED": "Auto",
            "COPY_DESC": "false",
            "CDP_ENABLE": "true",
            "lldpTransmit": "false",
            "lldpReceive": "false",
            "PORT_DUPLEX_MODE": "auto",
            "DISABLE_LACP_SUSPEND": "false",
            "ENABLE_LACP_VPC_CONV": "false",
            "LACP_PORT_PRIO": 32768,
            "LACP_RATE": "normal",
            "ADMIN_STATE": admin,
            "ENABLE_PFC": "false",
            "ENABLE_QOS": "false",
            "QOS_POLICY": "",
            "qosStatsSuppressed": "false",
            "QUEUING_POLICY": "",
            "queuingStats": "false",
            "aclFilter": "",
            "ENABLE_MIRROR_CONFIG": "false",
            "PVLAN_MODE": "host",
            "MAPPING_LIST": "",
            "ASSOCIATION_LIST": wire,
            "PEER1_PCID": "10",
            "PEER2_PCID": "10",
            "PEER1_MEMBER_INTERFACES": M1,
            "PEER2_MEMBER_INTERFACES": M2,
            "PEER1_PO_DESC": descs[0],
            "PEER2_PO_DESC": descs[1],
            "PEER1_PO_CONF": "",
            "PEER2_PO_CONF": "",
            "PEER1_PVLAN_ALLOWED_VLANS": "",
            "PEER2_PVLAN_ALLOWED_VLANS": "",
            "PEER1_PVLAN_NATIVE_VLAN": "",
            "PEER2_PVLAN_NATIVE_VLAN": "",
            "INTF_NAME": VPC,
            "SERIAL_NUMBER": PAIR,
        }
        parent.update(self.parent_metadata)
        self.parents[VPC] = {"policy": VPC_HOST, "nvPairs": parent}
        self._expand_children(parent)
        return self

    def _expand_children(self, parent):
        """What the templates are PREDICTED to do on save (HOST 590-780): one child Po and one flipped member per peer."""
        for index, serial in enumerate((SN1, SN2)):
            n = index + 1
            port = parent["PEER%d_MEMBER_INTERFACES" % n]
            po = "port-channel" + parent["PEER%d_PCID" % n]
            self.nodes[serial][po] = {
                "policy": VPC_PO,
                "source": VPC,
                "nvPairs": {
                    "PO_ID": po,
                    "PRIMARY_INTF": VPC,
                    "PVLAN_MODE": parent["PVLAN_MODE"],
                    "ASSOCIATION_LIST": parent["ASSOCIATION_LIST"],
                    # VPC-MODES-E1: the other lists and the per-peer PVLAN native/allowed reach the child too (HOST 604-680 [SRC])
                    "MAPPING_LIST": parent.get("MAPPING_LIST", ""),
                    "PVLAN_NATIVE_VLAN": parent.get("PEER%d_PVLAN_NATIVE_VLAN" % n, ""),
                    "PVLAN_ALLOWED_VLANS": parent.get("PEER%d_PVLAN_ALLOWED_VLANS" % n, ""),
                    "ADMIN_STATE": parent["ADMIN_STATE"],
                    "DESC": parent["PEER%d_PO_DESC" % n],
                    "BPDUGUARD_ENABLED": parent["BPDUGUARD_ENABLED"],
                    "PORTTYPE_FAST_ENABLED": parent["PORTTYPE_FAST_ENABLED"],
                    "MTU": parent["MTU"],
                    "CONF": "",
                },
            }
            old = self.nodes[serial].get(port, {"nvPairs": {}})["nvPairs"]
            self.nodes[serial][port] = {
                "policy": PO_MEMBER,
                "source": VPC,
                "nvPairs": {
                    "PO_ID": po,
                    "PRIMARY_INTF": VPC,
                    "PC_MODE": parent["PC_MODE"],
                    "PVLAN_MODE": parent["PVLAN_MODE"],
                    "CDP_ENABLE": "true",
                    "lldpTransmit": "false",
                    "lldpReceive": "false",
                    "LACP_PORT_PRIO": "32768",
                    "LACP_RATE": "normal",
                    "DESC": old.get("DESC", ""),
                    "CONF": "",
                    "ADMIN_STATE": str(old.get("ADMIN_STATE", "false")).lower(),
                    "INTF_NAME": port,
                },
            }

    # ---- test helpers
    def writes(self):
        return [c for c in self.calls if c[0] in ("POST", "PUT", "DELETE") and "networkAttachments/query" not in c[1] and PREVIEW_MARK not in c[1]]

    def creates(self):
        return [c for c in self.calls if c[0] == "POST" and c[1].endswith(GLOBAL_IF)]

    def deploys(self):
        return [c for c in self.calls if c[0] == "POST" and c[1].endswith(DEPLOY)]

    def modifies(self):
        return [c for c in self.calls if c[0] == "POST" and c[1].endswith(MODIFY)]

    def markdeletes(self):
        return [c for c in self.calls if c[0] == "DELETE" and c[1].endswith(MARKDELETE)]

    def previews_asked(self):
        return [c[1].split("config-preview/")[1].split("?")[0] for c in self.calls if PREVIEW_MARK in c[1]]

    # ---- transport
    def __call__(self, mod, method, path, data=None):
        self.calls.append((method, path, data))
        for mark in self.read_failures:
            if mark in path:
                return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
        if "vpcpair_serial_number" in path:
            return ok({"vpc_pair_sn": PAIR})
        if PREVIEW_MARK in path:
            serial = path.split("config-preview/")[1].split("?")[0]
            queue = self.vpc_previews.setdefault(serial, [])
            nxt = queue.pop(0) if queue else preview([], serial=serial)
            return nxt(path) if callable(nxt) else nxt
        if "/control/policies/switches/" in path:
            serial = path.rsplit("/", 1)[1]
            flaky = self.policy_failures.get(serial)
            if self.deployed and flaky:
                if flaky.pop(0):
                    return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
            if self.policies_override is not None:
                return copy.deepcopy(self.policies_override)
            return ok(self._peer_policies(serial))
        if "/rest/interface/detail?serialNumber=" in path:
            return ok(self._peer_summary(path.split("serialNumber=")[1]))
        if "/rest/interface?serialNumber=" in path:
            serial = path.split("serialNumber=")[1].split("&")[0]
            entries = self._peer_details(serial)
            if "&ifName=" in path:
                name = path.split("&ifName=")[1]
                return ok([e for e in entries if e["interfaces"][0]["ifName"].lower() == name.lower()])
            return ok(entries)
        if method == "POST" and path.endswith(GLOBAL_IF):
            resp = self.create_responses.pop(0) if self.create_responses else ok({})
            body = json.loads(data)
            if resp.get("RETURN_CODE") in (200, 207):
                for payload in body if isinstance(body, list) else [body]:
                    for intf in payload["interfaces"]:
                        if payload["policy"] == VPC_HOST:
                            self.parents[intf["ifName"]] = {"policy": VPC_HOST, "nvPairs": copy.deepcopy(intf["nvPairs"])}
                            if self.children_on_save:
                                self._expand_children(intf["nvPairs"])
            return resp
        if method == "POST" and path.endswith(MODIFY):
            resp = self.modify_responses.pop(0) if self.modify_responses else None
            body = json.loads(data)
            if resp is None:
                items = [
                    {"reportItemType": "SUCCESS", "message": "Interface updated successfully", "entity": "%s~%s" % (i["serialNumber"], i["ifName"])}
                    for p in body
                    for i in p["interfaces"]
                ]
                resp = {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": items}
            failing = [i for p_ in body for i in p_["interfaces"] if i["serialNumber"] in self.member_modify_fail]
            if failing:
                resp = {
                    "RETURN_CODE": 207,
                    "MESSAGE": "Multi-Status",
                    "DATA": [
                        {"reportItemType": "ERROR", "message": "member modify refused", "entity": "%s~%s" % (i["serialNumber"], i["ifName"])} for i in failing
                    ],
                }
            if all(str(i.get("reportItemType")).upper() == "SUCCESS" for i in resp.get("DATA") or [{}]):
                for payload in body:
                    for intf in payload["interfaces"]:
                        if payload["policy"] == VPC_HOST:
                            self.parents[intf["ifName"]] = {"policy": VPC_HOST, "nvPairs": copy.deepcopy(intf["nvPairs"])}
                            self._expand_children(intf["nvPairs"])
                        elif intf["serialNumber"] in self.nodes:  # a standalone interface (the released member): store what was sent
                            self.nodes[intf["serialNumber"]][intf["ifName"]] = {"policy": payload["policy"], "nvPairs": copy.deepcopy(intf["nvPairs"])}
            return resp
        if method == "DELETE" and path.endswith(MARKDELETE):
            self.markdeleted = True
            for intf in json.loads(data):
                parent = self.parents.pop(intf["ifName"], None)
                if parent and "PEER1_MEMBER_INTERFACES" in parent["nvPairs"]:
                    for index, serial in enumerate((SN1, SN2)):
                        n = index + 1
                        po = "port-channel" + parent["nvPairs"]["PEER%d_PCID" % n]
                        port = parent["nvPairs"]["PEER%d_MEMBER_INTERFACES" % n]
                        self.nodes[serial].pop(po, None)
                        if self.release_on_delete:
                            nv = trunk_host_nv(port)
                            nv["ADMIN_STATE"] = "true" if self.release_admin_up else "false"
                            self.nodes[serial][port] = {"policy": TRUNK, "nvPairs": nv}
                        if self.children_marked_deleted:
                            self.summary_extra[serial].append(self._marked_deleted_entry(serial, po))
                            self.policies_extra[serial].append(
                                {
                                    "entityName": po,
                                    "entityType": "INTERFACE",
                                    "templateName": "interface_delete",
                                    "source": self.marked_source if self.marked_source is not None else VPC.lower(),
                                    "deleted": True,
                                    "policyId": pid(serial, po) + "-del",
                                    "serialNumber": serial,
                                }
                            )
            if self.markdelete_responses:
                return self.markdelete_responses.pop(0)
            return ok(
                {
                    "message": "Interface deleted successfully",
                    "value": [{"interfaceType": "INTERFACE_VPC", "serialNumber": PAIR, "IfName": i["ifName"]} for i in json.loads(data)],
                }
            )
        self.calls.pop()  # the parent harness records the call itself
        resp = super(VpcController, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(DEPLOY):  # the deploy completes the deletion: the marked-for-deletion listings go away
            for serial in (SN1, SN2):
                self.summary_extra[serial] = [e for e in self.summary_extra[serial] if str(e.get("markDeleted")) != "True"]
                self.policies_extra[serial] = [p_ for p_ in self.policies_extra[serial] if p_.get("templateName") != "interface_delete"]
        return resp

    # ---- peer views
    def _peer_policies(self, serial):
        out = []
        for name, d in sorted(self.nodes[serial].items()):
            out.append(
                {
                    "entityName": name,
                    "entityType": "INTERFACE",
                    "templateName": d["policy"],
                    "source": d.get("source", ""),
                    "deleted": False,
                    "policyId": pid(serial, name),
                    "priority": 500,
                    "serialNumber": serial,
                    "autoGenerated": True,
                }
            )
            if d["policy"] == PO_MEMBER and self.inherited_child:
                out.append(
                    {
                        "entityName": name,
                        "entityType": "INTERFACE",
                        "templateName": "int_eth",
                        "source": d.get("source", ""),
                        "deleted": False,
                        "policyId": pid(serial, name) + "-inh",
                        "priority": 540,
                        "serialNumber": serial,
                        "autoGenerated": True,
                    }
                )
        if self.list_parent_policy:
            for name in self.parents:
                out.append(
                    {
                        "entityName": name,
                        "entityType": "INTERFACE",
                        "templateName": VPC_HOST,
                        "source": "",
                        "deleted": False,
                        "policyId": "POLICY-PARENT",
                        "priority": 500,
                        "serialNumber": PAIR,
                        "autoGenerated": False,
                    }
                )
        return out + copy.deepcopy(self.policies_extra.get(serial, []))

    def _summary_entry(self, serial, name, d, status):
        physical = d["policy"] in (TRUNK, PO_MEMBER, "int_access_host", "int_routed_host")  # VPC-MODES-E1: prepared members are physical
        return {
            "ifName": name,
            "serialNo": serial,
            "fabricName": FABRIC,
            "ifType": "INTERFACE_ETHERNET" if physical else "INTERFACE_PORT_CHANNEL",
            "isPhysical": "True" if physical else "False",
            "deletable": "True",
            "editAllowed": "True",
            "markDeleted": "False",
            "alias": "",
            "deleteReason": None,
            "complianceStatus": status,
            "mode": "trunk",
            "underlayPolicies": [
                {
                    "source": d.get("source", ""),
                    "templateName": d["policy"],
                    "policyId": pid(serial, name),
                    "entityName": name,
                    "entityType": "INTERFACE",
                    "serialNumber": serial,
                }
            ],
            "interfaces": [{"nvPairs": {}}],
        }

    def _marked_deleted_entry(self, serial, name):
        """MEASURED (L1-E4 live F) for the child of a vPC, as for a deployed regular Po (F-HR-deployed): listed until the deploy, marked for
        deletion, ONE `interface_delete` policy whose source is the PARENT vPC (lower case `vpc10`)."""
        return {
            "ifName": name,
            "serialNo": serial,
            "fabricName": FABRIC,
            "ifType": "INTERFACE_PORT_CHANNEL",
            "isPhysical": "False",
            "deletable": "True",
            "editAllowed": "True",
            "markDeleted": "True",
            "alias": "",
            "deleteReason": None,
            "complianceStatus": "NA",
            "underlayPolicies": [
                {
                    "source": self.marked_source if self.marked_source is not None else VPC.lower(),
                    "templateName": "interface_delete",
                    "policyId": pid(serial, name) + "-del",
                    "entityName": name,
                    "entityType": "INTERFACE",
                    "serialNumber": serial,
                }
            ],
            "interfaces": [{"nvPairs": {}}],
        }

    def _peer_summary(self, serial):
        out = []
        for name, d in sorted(self.nodes[serial].items()):
            out.append(self._summary_entry(serial, name, d, self.compliance_by.get((serial, name), "In-Sync")))
        out.extend(copy.deepcopy(self.summary_extra.get(serial, [])))
        if self.vpc_in_summary and serial in (SN1, SN2):
            for name in self.parents:
                out.append(
                    {
                        "ifName": name,
                        "serialNo": PAIR,
                        "fabricName": FABRIC,
                        "ifType": "INTERFACE_VPC",
                        "isPhysical": "False",
                        "deletable": "True",
                        "editAllowed": "True",
                        "markDeleted": "False",
                        "alias": "",
                        "deleteReason": None,
                        "complianceStatus": "In-Sync",
                        "mode": "trunk",
                        "underlayPolicies": [
                            {
                                "source": "",
                                "templateName": VPC_HOST,
                                "policyId": "POLICY-PARENT",
                                "entityName": name,
                                "entityType": "INTERFACE",
                                "serialNumber": PAIR,
                            }
                        ],
                        "interfaces": [{"nvPairs": {}}],
                    }
                )
        return out

    def _peer_details(self, serial):
        out = []
        for name, d in sorted(self.nodes[serial].items()):
            out.append({"policy": d["policy"], "interfaces": [{"serialNumber": serial, "ifName": name, "nvPairs": copy.deepcopy(d["nvPairs"])}]})
        if serial in (SN1, SN2):
            for name, d in self.parents.items():
                out.append({"policy": d["policy"], "interfaces": [{"serialNumber": PAIR, "ifName": name, "nvPairs": copy.deepcopy(d["nvPairs"])}]})
        return out


def run_vpc(ctrl, config, state="merged", check_mode=False, bulk=True, version=(12, NDFC), fabric_admin="false", patch_version=None):
    """Drive the real main() against a pair of switches. Returns ("exit"|"fail", result dict). Every call builds a NEW module
    instance, exactly as two Ansible invocations would: nothing but the controller's state carries over.
    patch_version is omitted from module args unless given: vPC PVLAN needs no patch context."""
    args = {"state": state, "fabric": FABRIC, "config": config, "check_deploy": False}
    if patch_version is not None:
        args["patch_version"] = patch_version
    if check_mode:
        args["_ansible_check_mode"] = True
    patches = [
        patch.object(basic.AnsibleModule, "exit_json", exit_json),
        patch.object(basic.AnsibleModule, "fail_json", fail_json),
        patch.object(module, "get_fabric_inventory_details", return_value=copy.deepcopy(INVENTORY)),
        patch.object(module, "get_ip_sn_dict", return_value=({IP1: SN1, IP2: SN2}, {})),
        patch.object(module, "dcnm_get_ip_addr_info", side_effect=lambda m, sw, a, b: sw),
        patch.object(module, "dcnm_version_supported", return_value=version),
        patch.object(module, "dcnm_send", side_effect=ctrl),
        patch.object(module, "dcnm_get_bulk_api_support", return_value=bulk),
        patch.object(module, "get_fabric_details", return_value={"nvPairs": {"HOST_INTF_ADMIN_STATE": fabric_admin}}),
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


# ---------------------------------------------------------------- playbook items
def vpc_item(name="vpc10", deploy=True, switches=None, **profile):
    prof = {
        "mode": "pvlan",
        "pvlan_mode": "host",
        "peer1_members": [M1],
        "peer2_members": [M2],
        "peer1_pcid": 10,
        "peer2_pcid": 10,
        "admin_state": False,
        "pvlan_association": [{"primary_vlan": PRIMARY, "secondary_vlan": SECONDARY}],
    }
    prof.update(profile)
    return {"name": name, "type": "vpc", "switch": list(switches or [IP1, IP2]), "deploy": deploy, "profile": prof}


def vpc_del_item(deploy=True):
    return {"name": "vpc10", "type": "vpc", "switch": [IP1, IP2], "deploy": deploy}


# ---------------------------------------------------------------- SYNTHETIC device/controller stanzas (from the templates)
def po_stanza(pair=(PRIMARY, SECONDARY), shut=True, desc=None):
    lines = [
        "interface port-channel10",
        "  switchport",
        "  switchport mode private-vlan host",
        "  switchport private-vlan host-association %d %d" % pair,
        "  mtu 9216",
        "  vpc 10",
        "  spanning-tree bpduguard enable",
        "  spanning-tree port type edge trunk",
    ]
    if desc:
        lines.append("  description %s" % desc)
    lines.append("  shutdown" if shut else "  no shutdown")
    return lines


def member_running_baseline(port):
    return [
        "interface %s" % port,
        "  switchport",
        "  switchport mode trunk",
        "  switchport trunk allowed vlan none",
        "  spanning-tree port type edge trunk",
        "  mtu 9216",
        "  shutdown",
    ]


def member_after(port, pair=(PRIMARY, SECONDARY), pc_mode="active"):
    return [
        "interface %s" % port,
        "  switchport",
        "  switchport mode private-vlan host",
        "  switchport private-vlan host-association %d %d" % pair,
        "  mtu 9216",
        "  channel-group 10 mode %s" % pc_mode,  # the PERSISTED form (MEASURED for a regular Po): no `force`
        "  shutdown",
    ]


def create_pending(port, pair=(PRIMARY, SECONDARY), desc=None):
    """The pending of a vPC creation on ONE peer. The member part has the MEASURED shape of a regular host Po (H1 preview): the member's own trunk
    edge line goes away and the join is the COMMAND `channel-group N force mode M`; the PVLAN mode and list arrive with it (they are NOT separate
    pending lines). SIMULATED for a vPC."""
    lowered = port.lower()
    return po_stanza(pair, desc=desc) + [
        "interface %s" % lowered,
        "  no spanning-tree port type edge trunk",
        "configure terminal",
        "interface %s" % lowered,
        "  channel-group 10 force mode active",
        "  shutdown",
        "configure terminal",
    ]


def create_preview(serial, port, pair=(PRIMARY, SECONDARY), desc=None):
    """Fresh preview of ONE peer after the vPC intent was saved (SYNTHETIC)."""
    return preview(
        create_pending(port, pair, desc), serial=serial, running=member_running_baseline(port), expected=po_stanza(pair, desc=desc) + member_after(port, pair)
    )


def create_previews(ctrl, pair=(PRIMARY, SECONDARY), descs=(None, None)):
    ctrl.vpc_previews[SN1] = [create_preview(SN1, M1, pair, descs[0])]
    ctrl.vpc_previews[SN2] = [create_preview(SN2, M2, pair, descs[1])]


def converged_preview(serial, port, pair=(PRIMARY, SECONDARY), desc=None):
    """Both configurations equal and empty pending: the deployed, coherent state of one peer."""
    return preview(
        [], serial=serial, running=po_stanza(pair, desc=desc) + member_after(port, pair), expected=po_stanza(pair, desc=desc) + member_after(port, pair)
    )


def converged_previews(ctrl, pair=(PRIMARY, SECONDARY), times=1):
    ctrl.vpc_previews[SN1] = [converged_preview(SN1, M1, pair) for _i in range(times)]
    ctrl.vpc_previews[SN2] = [converged_preview(SN2, M2, pair) for _i in range(times)]


def update_pending(port, old, new):
    """An association change of an EXISTING vPC (SIMULATED; MEASURED shape for a regular Po, H4): ONLY the child Po's block carries the change; the
    member's device state follows its port-channel, so the member has NO pending."""
    return [
        "interface port-channel10",
        "  no switchport private-vlan host-association %d %d" % old,
        "  switchport private-vlan host-association %d %d" % new,
    ]


def update_preview(serial, port, old, new):
    return preview(
        update_pending(port, old, new), serial=serial, running=po_stanza(old) + member_after(port, old), expected=po_stanza(new) + member_after(port, new)
    )


def pc_mode_preview(serial, port, desc=None, old="active", new="passive"):
    """Only the member's channel-group mode changes (SYNTHETIC): the child Po is untouched."""
    return preview(
        ["interface %s" % port, "  no channel-group 10 mode %s" % old, "  channel-group 10 mode %s" % new],  # NOT MEASURED, INFERRED
        serial=serial,
        running=po_stanza(desc=desc) + member_after(port, pc_mode=old),
        expected=po_stanza(desc=desc) + member_after(port, pc_mode=new),
    )


def description_preview(serial, port, old, new):
    """Only the description of the child Po changes (SYNTHETIC)."""
    pending = ["interface port-channel10"] + (["  no description %s" % old] if old else []) + ["  description %s" % new]
    return preview(pending, serial=serial, running=po_stanza(desc=old) + member_after(port), expected=po_stanza(desc=new) + member_after(port))


def delete_preview(serial, port, pair=(PRIMARY, SECONDARY)):
    released = [
        "interface %s" % port,
        "  switchport",
        "  switchport mode trunk",
        "  switchport trunk allowed vlan none",
        "  spanning-tree port type edge trunk",
        "  mtu 9216",
        "  shutdown",
    ]
    pend = [
        "no interface port-channel10",
        "interface %s" % port,
        "  no switchport mode private-vlan host",
        "  no switchport private-vlan host-association %d %d" % pair,
        "  no channel-group 10 force mode active",
        "  switchport mode trunk",
        "  switchport trunk allowed vlan none",
        "  spanning-tree port type edge trunk",
    ]
    return preview(pend, serial=serial, running=po_stanza(pair) + member_after(port, pair), expected=released)


def delete_previews(ctrl, pair=(PRIMARY, SECONDARY)):
    ctrl.vpc_previews[SN1] = [delete_preview(SN1, M1, pair)]
    ctrl.vpc_previews[SN2] = [delete_preview(SN2, M2, pair)]


def baseline_ctrl():
    return VpcController().seed_baseline()


def created_ctrl(**kw):
    """A coherent, created and deployed vPC, seeded BY HAND (not produced by a module run): the next invocation has no memory."""
    ctrl = VpcController().seed_baseline().seed_vpc(**kw)
    ctrl.next_invocation()
    return ctrl


def release_only(ctrl, count=2):
    """The ONLY member writes of a vPC deletion are the E4 release corrections (MEASURED for a regular Po, INFERRED for a vPC): per peer ONE legacy
    modify of the released int_trunk_host with ADMIN_STATE "false", all BEFORE the deploy. Nothing is written after the deploy: no repair."""
    bodies = [json.loads(c[2]) for c in ctrl.modifies()]
    assert len(bodies) == count, bodies
    for body in bodies:
        for payload in body:
            assert payload["policy"] == TRUNK
            for intf in payload["interfaces"]:
                assert intf["nvPairs"]["ADMIN_STATE"] == "false" and intf["ifName"] in (M1, M2)
    order = ctrl.order()
    if "DEPLOY" in order and "MODIFY" in order:
        assert max(i for i, x in enumerate(order) if x == "MODIFY") < order.index("DEPLOY"), "a member write after the deploy"
    return bodies
