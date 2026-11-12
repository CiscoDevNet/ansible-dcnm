"""The minimal two-serial extension of the existing PVLAN harness.

NOT LIVE TESTED. Real main(); only the external boundary is mocked, through the EXISTING harness
(helpers/ethernet_controller.FakeController) plus the smallest subclass that teaches it a PAIR of switches: state per serial, the
vPC parent that appears on both peers, per-serial previews/policy lists and a vPC create/delete. No new framework or simulator.

Shapes taken from the regular Po measurements (fixtures/pvlan_po_create_update.json#pvlan_po_h1_measured, NDFC 12.6.0.267):
  MEASURED for a REGULAR host Po, SIMULATED here for a vPC: the member joins through the pending COMMAND
  `channel-group N force mode M` while the controller's expected member and the device keep the PERSISTED `channel-group N mode M`;
  an existing member inherits its Po's association change with NO member pending; a deployed member leaves with the command form
  `no channel-group N force mode M`; the mark-delete answers 200/OK 'Interface deleted successfully' with ONE `value` item; the
  controller releases the member as int_trunk_host with ADMIN_STATE "true".
  None of this was observed for a vPC here: it is an extrapolation for a live case to measure.

Three kinds of data, never mixed:
  * contract of the source   -- what the captured templates and the existing module code say (cited in the tests);
  * SYNTHETIC fixture        -- every preview/summary/policy shape below is written BY HAND from those templates. The fake
                                 applies on a create/delete exactly what the templates are PREDICTED to do (children per peer,
                                 member flip, member release); that prediction is the hypothesis under test, not a controller
                                 measurement;
  * future live measurement  -- nothing here certifies the controller.
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

from ...dcnm_module import set_module_args
from .ethernet_controller import (
    FABRIC,
    NDFC,
    PREVIEW_MARK,
    TRUNK,
    FakeController,
    ok,
    preview,
    trunk_host_nv,
)
import collections
from . import port_channel_release as G4

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
    (ip, {"logicalName": "sw-%d" % (i + 1), "serialNumber": sn, "isVpcConfigured": "True", "vpcDomain": 10, "switchRole": "leaf", "managable": "True",
          "ccStatus": "In-Sync"})
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
        self.summary_failures = {}  # serial -> list consumed per interface-summary read AFTER a deploy (True = HTTP 500)
        self.create_responses = []
        self.children_on_save = True  # [INF] the parent's add() writes the children when the intent is saved (HOST 590-600): L1 measures it
        self.release_on_delete = True  # [UNK] V6: the members return to int_trunk_host after the vPC is deleted
        self.release_admin_up = True  # MEASURED for a regular Po, INFERRED for a vPC: the released member is int_trunk_host ADMIN_STATE "true"
        self.markdelete_responses = []  # consumed in order; default: the measured Po answer with the PAIR identity (INFERRED for a vPC)
        self.member_modify_fail = set()  # serials whose member modify answers an ERROR item
        self.children_marked_deleted = False  # MEASURED: the deleted vPC's child Po stays listed as `interface_delete` until the deploy
        self.marked_source = None  # the `interface_delete` source; None = the parent vPC (MEASURED: `vpc10`, lower case); set to model a foreign owner
        self.parent_metadata = {"createVpc": "true"}  # MEASURED: the controller adds `createVpc` "true" to the created parent
        self.list_parent_policy = False  # [UNK] V2: whether the parent policy is listed on a peer
        self.vpc_in_summary = True  # [UNK] V0: whether the vPC is an entry of the interface summary
        # MEASURED (NDFC 12.6.0.267): after the vPC's mark-delete the PARENT stays listed on both peers' summaries,
        # markDeleted True, Out-of-Sync, no underlay policy. Off by default: the older harness shape.
        self.parent_marked_listed = False
        self.inherited_child = True  # the 'Inherited Commands' int_eth child of every member (HOST 755-780)
        self.summary_extra = {SN1: [], SN2: []}  # entries listed by the interface summary of a peer and by nothing else
        self.compliance_by = {}  # (serial, ifName) -> status
        self.markdeleted = False
        # False = the CORRECTED parent (qosPolicy/queuingPolicy locals: the reference int_vpc_trunk_host and every Engineering
        # set) hands ENABLE_QOS/QOS_POLICY/ENABLE_PFC/QUEUING_POLICY to both children. True = the revision INSTALLED on the test ND
        # (MEASURED, live S1): its UnboundLocalError resets those four to false/'' on every save, while queuingStats and
        # qosStatsSuppressed (interfaceOptions) still follow the parent.
        self.defective_qos_template = False

    # ---- seeding (explicit state, never produced by the code under test)
    def seed_baseline(self):
        for serial, port in ((SN1, M1), (SN2, M2)):
            nv = trunk_host_nv(port)
            nv["ADMIN_STATE"] = "false"
            self.nodes[serial][port] = {"policy": TRUNK, "nvPairs": nv}
        return self

    def seed_vpc(self, association=((PRIMARY, SECONDARY),), descs=("", ""), admin="false", pcids=("10", "10")):
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
            "PEER1_PCID": str(pcids[0]),
            "PEER2_PCID": str(pcids[1]),
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
            ports = parent["PEER%d_MEMBER_INTERFACES" % n].split(",")
            po = "port-channel" + parent["PEER%d_PCID" % n]
            self.nodes[serial][po] = {
                "policy": VPC_PO,
                "source": VPC,
                "nvPairs": {
                    "PO_ID": po,
                    "PRIMARY_INTF": VPC,
                    "PVLAN_MODE": parent["PVLAN_MODE"],
                    "ASSOCIATION_LIST": parent["ASSOCIATION_LIST"],
                    # The other lists and the per-peer PVLAN native/allowed reach the child too (HOST 604-680 [SRC])
                    "MAPPING_LIST": parent.get("MAPPING_LIST", ""),
                    "PVLAN_NATIVE_VLAN": parent.get("PEER%d_PVLAN_NATIVE_VLAN" % n, ""),
                    "PVLAN_ALLOWED_VLANS": parent.get("PEER%d_PVLAN_ALLOWED_VLANS" % n, ""),
                    "ADMIN_STATE": parent["ADMIN_STATE"],
                    "DESC": parent["PEER%d_PO_DESC" % n],
                    "BPDUGUARD_ENABLED": parent["BPDUGUARD_ENABLED"],
                    "PORTTYPE_FAST_ENABLED": parent["PORTTYPE_FAST_ENABLED"],
                    "MTU": parent["MTU"],
                    # RC1: the child carries its peer's freeform (HOST 647/677 [SRC]: "CONF": peerNConf).
                    "CONF": parent.get("PEER%d_PO_CONF" % n, ""),
                },
            }
            # The other parent fields the template hands to each child (HOST 636-688 [SRC]), with its defaults.
            for key, default in (
                ("spanningTreePortType", "no"),
                ("SPEED", "Auto"),
                ("PORT_DUPLEX_MODE", "auto"),
                ("DISABLE_LACP_SUSPEND", "false"),
                ("ENABLE_LACP_VPC_CONV", "false"),
                ("ENABLE_PFC", "false"),
                ("QUEUING_POLICY", ""),
                ("queuingStats", "false"),
                ("aclFilter", ""),
                # Ingress QoS (HOST 652-657 / 682-687)
                ("ENABLE_QOS", "false"),
                ("qosStatsSuppressed", "false"),
            ):
                self.nodes[serial][po]["nvPairs"][key] = parent.get(key, default)
            child = self.nodes[serial][po]["nvPairs"]
            # The corrected parent hands QOS_POLICY only with QoS enabled (qosPolicy; no AI/ML fabric in this harness)
            child["QOS_POLICY"] = parent.get("QOS_POLICY", "") if str(parent.get("ENABLE_QOS", "false")).lower() == "true" else ""
            if self.defective_qos_template:
                child.update({"ENABLE_PFC": "false", "ENABLE_QOS": "false", "QOS_POLICY": "", "QUEUING_POLICY": ""})
            for port in ports:
                old = self.nodes[serial].get(port, {"nvPairs": {}})["nvPairs"]
                self.nodes[serial][port] = {
                    "policy": PO_MEMBER,
                    "source": VPC,
                    "nvPairs": {
                        "PO_ID": po,
                        "PRIMARY_INTF": VPC,
                        "PC_MODE": parent["PC_MODE"],
                        "PVLAN_MODE": parent["PVLAN_MODE"],
                        # CDP, LLDP and LACP come from the parent (HOST 764-768 / 854-858 [SRC]); DESC is the peer's
                        # PEERn_PO_DESC when COPY_DESC is true, else the member's own (HOST 750-752 [SRC]).
                        "CDP_ENABLE": parent.get("CDP_ENABLE", "true"),
                        "lldpTransmit": parent.get("lldpTransmit", "false"),
                        "lldpReceive": parent.get("lldpReceive", "false"),
                        "LACP_PORT_PRIO": str(parent.get("LACP_PORT_PRIO", "32768")),
                        "LACP_RATE": parent.get("LACP_RATE", "normal"),
                        "DESC": parent.get("PEER%d_PO_DESC" % n, "") if str(parent.get("COPY_DESC", "false")).lower() == "true" else old.get("DESC", ""),
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
            flaky = self.summary_failures.get(path.split("serialNumber=")[1])
            if self.deployed and flaky and flaky.pop(0):
                return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
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
                        ports = parent["nvPairs"]["PEER%d_MEMBER_INTERFACES" % n].split(",")
                        self.nodes[serial].pop(po, None)
                        if self.release_on_delete:
                            for port in ports:
                                nv = trunk_host_nv(port)
                                nv["ADMIN_STATE"] = "true" if self.release_admin_up else "false"
                                self.nodes[serial][port] = {"policy": TRUNK, "nvPairs": nv}
                        if self.parent_marked_listed:
                            self.summary_extra[serial].append({
                                "ifName": intf["ifName"], "serialNo": PAIR, "fabricName": FABRIC, "ifType": "INTERFACE_VPC", "isPhysical": "False",
                                "deletable": "True", "editAllowed": "True", "markDeleted": "True", "alias": "", "deleteReason": None,
                                "complianceStatus": "Out-of-Sync", "underlayPolicies": []})
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
        if method == "POST" and path.endswith(DEPLOY):
            self._deploy_completed(data)
        return resp

    def _deploy_completed(self, data):
        """The deploy completes the deletion: the marked-for-deletion listings go away (every listing of the one default pair)."""
        for serial in (SN1, SN2):
            self.summary_extra[serial] = [e for e in self.summary_extra[serial] if str(e.get("markDeleted")) != "True"]
            self.policies_extra[serial] = [p_ for p_ in self.policies_extra[serial] if p_.get("templateName") != "interface_delete"]

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
        physical = d["policy"] in (TRUNK, PO_MEMBER, "int_access_host", "int_routed_host")  # prepared members are physical
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
        """MEASURED for the child of a vPC, as for a deployed regular Po (F-HR-deployed): listed until the deploy, marked for
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
    """The pending of a vPC creation on ONE peer. The member part has the MEASURED shape of a regular host Po (preview): the member's own trunk
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


PAIRS = ((SN1, SN2), ("FDO00000003", "FDO00000004"))
IPS = {SN1: IP1, SN2: IP2, "FDO00000003": "10.0.0.3", "FDO00000004": "10.0.0.4"}


def subst(lines, k, pcid=None):
    """The harness stanzas for vPC id `k`; `pcid` is the peer's own port-channel number when it differs from the vPC id."""
    pcid = k if pcid is None else pcid
    return [x.replace("port-channel10", "port-channel%d" % pcid).replace("vpc 10", "vpc %d" % k).replace("channel-group 10", "channel-group %d" % pcid)
            for x in lines]


class MultiVpc(VpcController):
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
        self.pcids = {}  # (pair serial, name) -> (peer1 pcid, peer2 pcid) when they differ from the vPC id
        self.deployed_vpcs, self.deleted_vpcs = set(), set()
        self.ready_round = {}     # (serial, ifName) -> waits after which the summary says In-Sync (None = never)
        self.sleep_log = []
        self.post_fail = {}       # (kind, serial) -> number of post-deploy GETs of that kind answered HTTP 500
        self.post_drop = {}       # serial -> {ifName} missing from post-deploy summaries
        self.post_dup = {}        # serial -> {ifName} listed twice in post-deploy summaries
        self.post_extra = {}      # serial -> summary entries listed only AFTER the last deploy
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
                nv = trunk_host_nv(port)
                nv["ADMIN_STATE"] = "false"
                self.nodes[serial][port] = {"policy": TRUNK, "nvPairs": nv}
        self.plan[(self.psn(pair), "vPC%d" % k)] = (k, pair, ports[0], ports[1])
        item = {"name": "vpc%d" % k, "type": "vpc", "switch": [IPS[pair[0]], IPS[pair[1]]], "deploy": deploy,
                "profile": {"mode": "pvlan", "pvlan_mode": "host", "peer1_members": ports[0], "peer2_members": ports[1], "peer1_pcid": k,
                            "peer2_pcid": k, "admin_state": False,
                            "pvlan_association": [{"primary_vlan": PRIMARY, "secondary_vlan": SECONDARY}]}}
        item["profile"].update(profile)
        self.pcids[(self.psn(pair), "vPC%d" % k)] = (item["profile"]["peer1_pcid"], item["profile"]["peer2_pcid"])
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
        global SN1, SN2, VPC, PAIR
        pair = self.plan[key][1]
        saved = (SN1, SN2, VPC, PAIR)
        SN1, SN2, VPC, PAIR = pair[0], pair[1], key[1], key[0]
        try:
            return fn()
        finally:
            SN1, SN2, VPC, PAIR = saved

    def _store_parent(self, intf, expand):
        key = self.key(intf["serialNumber"], intf["ifName"])
        nv = copy.deepcopy(intf["nvPairs"])
        nv.setdefault("INTF_NAME", intf["ifName"])
        self.parents[key] = {"policy": VPC_HOST, "nvPairs": nv}
        if expand:
            self._with_pair(key, lambda: VpcController._expand_children(self, nv))

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
        if self.deployed:
            out.extend(copy.deepcopy(self.post_extra.get(serial, [])))
        for key in self.parents:
            if serial in self.plan[key][1]:
                e = self._summary_entry(serial, key[1], {"policy": VPC_HOST}, "In-Sync")
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

    def _released(self, serial, port, k, pcid):
        """(pending lines after `no interface port-channelN`, expected lines) of a member the mark-delete released; the default is the
        trunk release of the vPC harness."""
        return subst(delete_preview(serial, port)["DATA"][0]["pendingConfig"][1:], k, pcid), member_running_baseline(port)

    def _preview_for(self, serial):
        pending, running, expected = [], [], []
        for key, (k, pair, m1, m2) in sorted(self.plan.items(), key=lambda x: x[1][0]):
            if serial not in pair:
                continue
            ports = m1 if serial == pair[0] else m2
            pcid = self.pcids.get(key, (k, k))[0 if serial == pair[0] else 1]
            # the child carries ITS pair's peer description (PEERn_PO_DESC of the parent stored under this pair identity)
            desc = (self.parents.get(key, {}).get("nvPairs") or {}).get("PEER%d_PO_DESC" % (1 if serial == pair[0] else 2)) or None
            po = subst(po_stanza(desc=desc), k, pcid)
            after = po + [x for p in ports for x in subst(member_after(p), k, pcid)]
            base = [x for p in ports for x in member_running_baseline(p)]
            if key in self.deleted_vpcs and key not in self.deployed_vpcs:
                released = [self._released(serial, p, k, pcid) for p in ports]
                pending += ["no interface port-channel%d" % pcid] + [x for withdrawn, _expected in released for x in withdrawn]
                running += after
                expected += [x for _withdrawn, member_expected in released for x in member_expected]
            elif key in self.parents and key not in self.deployed_vpcs:
                pending += po + [x for p in ports for x in subst(create_pending(p, desc=desc), k, pcid)[len(po):]]
                running += base
                expected += after
            elif key in self.parents:
                running += after
                expected += after
            else:
                running += base
                expected += base
        pending += self.extra_pending.get(serial, [])
        return preview(pending, serial=serial, running=running, expected=expected)

    def _deploy_completed(self, data):
        """A deploy completes the deletion of the vPCs it names, on THEIR pair only: the marked-for-deletion listings of another pair stay."""
        for item in json.loads(data):
            if "~" not in str(item.get("serialNumber")):
                continue
            source = str(item["ifName"]).lower()
            for serial in self.pair_of(item["serialNumber"].split("~")[0]):
                self.summary_extra[serial] = [e for e in self.summary_extra[serial] if not (
                    str(e.get("markDeleted")) == "True" and any(str(u.get("source")).lower() == source for u in e.get("underlayPolicies") or []))]
                self.policies_extra[serial] = [p_ for p_ in self.policies_extra[serial] if not (
                    p_.get("templateName") == "interface_delete" and str(p_.get("source")).lower() == source)]

    def __call__(self, mod, method, path, data=None):
        if "vpcpair_serial_number" in path:
            self.calls.append((method, path, data))
            return ok({"vpc_pair_sn": self.psn(self.pair_of(path.split("serial_number=")[1].split("&")[0]))})
        if PREVIEW_MARK in path:
            self.calls.append((method, path, data))
            return self._preview_for(path.split("config-preview/")[1].split("?")[0])
        if method == "GET" and self.deployed:
            kind = kind_of(path)
            serial = serial_of(path)
            if self.post_fail.get((kind, serial), 0) > 0:
                self.calls.append((method, path, data))
                self.post_fail[(kind, serial)] -= 1
                return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
        if method == "POST" and path.endswith(GLOBAL_IF):
            # the parent is stored under its PAIR identity; the children of THAT pair are expanded as the harness predicts
            self.calls.append((method, path, data))
            resp = self.create_responses.pop(0) if self.create_responses else ok({})
            body = json.loads(data)
            if resp.get("RETURN_CODE") in (200, 207):
                for payload in body if isinstance(body, list) else [body]:
                    assert payload["policy"] in (VPC_HOST, "int_loopback"), payload["policy"]  # a loopback keeps an overridden request non-empty
                    for intf in payload["interfaces"] if payload["policy"] == VPC_HOST else []:
                        self._store_parent(intf, self.children_on_save)
            return resp
        if method == "POST" and path.endswith(MODIFY):
            body = json.loads(data)
            if any(p_["policy"] == VPC_HOST for p_ in body):
                assert all(p_["policy"] == VPC_HOST for p_ in body) and not self.modify_responses
                self.calls.append((method, path, data))
                for payload in body:
                    for intf in payload["interfaces"]:
                        self._store_parent(intf, True)
                return {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": [
                    {"reportItemType": "SUCCESS", "message": "Interface updated successfully", "entity": "%s~%s" % (i["serialNumber"], i["ifName"])}
                    for p_ in body for i in p_["interfaces"]]}
        if method == "DELETE" and path.endswith(MARKDELETE):
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
        if method == "POST" and path.endswith(DEPLOY):
            for d in json.loads(data):
                if "~" in str(d.get("serialNumber")) and any(k[0] == d["serialNumber"] and k[1].lower() == str(d["ifName"]).lower() for k in self.plan):
                    self.deployed_vpcs.add(self.key(d["serialNumber"], d["ifName"]))  # a vPC outside the plan is a seeded conventional one
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
                          "switchRole": getattr(ctrl, "roles", {}).get(sn, "leaf"), "managable": "True"}) for i, sn in enumerate(sorted(ctrl.nodes)))
    args = {"state": state, "fabric": FABRIC, "config": config, "check_deploy": False}
    patches = [
        patch.object(basic.AnsibleModule, "exit_json", exit_json),
        patch.object(basic.AnsibleModule, "fail_json", fail_json),
        patch.object(module, "get_fabric_inventory_details", return_value=inv),
        patch.object(module, "get_ip_sn_dict", return_value=(dict((ip, v["serialNumber"]) for ip, v in inv.items()), {})),
        patch.object(module, "dcnm_get_ip_addr_info", side_effect=lambda m, sw, a, b: sw),
        patch.object(module, "dcnm_version_supported", return_value=(12, NDFC)),
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
    deploys = [i for i, c in enumerate(calls) if c[0] == "POST" and c[1].endswith(DEPLOY)]
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


def post_kinds(ctrl):
    return dict((k.split(" ", 2)[2], v) for k, v in phase_counts(ctrl).items() if k.startswith("post GET"))


# ------------------------------------------------------------------ IDENTITY: the same vPC name on two pairs (review of 80c37c8)
# The controller identifies a vPC by its PAIR serial + its name. vPC10 exists on both pairs, with the SAME member names on different serials
# and DIFFERENT expected values per pair (peer1 description), so a plan keyed by the name alone would judge one pair with the other's data.
PA, PB = PAIRS[0][0] + "~" + PAIRS[0][1], PAIRS[1][0] + "~" + PAIRS[1][1]


def same_name_on_two_pairs():
    ctrl = MultiVpc(2)
    config = [ctrl.add_vpc(10, 0, peer1_description="pair-a-p1"), ctrl.add_vpc(10, 1, peer1_description="pair-b-p1")]
    return ctrl, config


def _remap_line(line, pcid):
    return line.replace("port-channel10", "port-channel" + pcid).replace("channel-group 10", "channel-group " + pcid)


def _remap_answer(answer, pcid):
    if callable(answer):
        return lambda path, _a=answer: _remap_answer(_a(path), pcid)
    out = copy.deepcopy(answer)
    for entry in out.get("DATA") or []:
        for key in ("pendingConfig", "runningConfig", "expectedConfig"):
            if isinstance(entry.get(key), list):
                entry[key] = [_remap_line(x, pcid) for x in entry[key]]
    return out


def remap(ctrl, pcids):
    """Rewrite the queued previews of both peers for their own port-channel numbers."""
    for serial, pcid in ((SN1, pcids[0]), (SN2, pcids[1])):
        ctrl.vpc_previews[serial] = [_remap_answer(a, pcid) for a in ctrl.vpc_previews.get(serial, [])]
    return ctrl


def seeded(pcids, **kw):
    return created_ctrl(pcids=pcids, **kw)


def sent_nv(ctrl):
    body = json.loads(ctrl.creates()[0][2])
    body = body[0] if isinstance(body, list) else body
    return body["interfaces"][0]["nvPairs"]


PEERS = ((SN1, M1), (SN2, M2))


def without_mtu(lines):
    return [l for l in lines if l.strip() != "mtu 9216"]


def releases(result):
    return [r for r in result.get("pvlan_vpc_release") or [] if "member_write" in r or "member_writes" in r]


# ================================================================== G3: the FRESH release of each member models the deletion
class ReleaseMtu(VpcController):
    """The controller releases each member with the MTU given per serial (default from a port-channel intent, as measured), SYNTHETIC."""

    def __init__(self, mtu, admin=None):
        super(ReleaseMtu, self).__init__()
        self.release_mtu = mtu
        self.release_admin = admin or {}

    def __call__(self, mod, method, path, data=None):
        resp = super(ReleaseMtu, self).__call__(mod, method, path, data)
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            for serial, port in PEERS:
                nv = self.nodes[serial][port]["nvPairs"]
                nv["MTU"] = self.release_mtu.get(serial, nv["MTU"])
                if serial in self.release_admin:
                    nv["ADMIN_STATE"] = self.release_admin[serial]
        return resp


def release_ctrl(mtu=None, admin=None):
    ctrl = ReleaseMtu(mtu or {}, admin).seed_baseline().seed_vpc()
    ctrl.next_invocation()
    return ctrl


def released_delete_preview(serial, port, jumbo):
    """The delete preview of ONE peer: released stanza at the fresh MTU; for a default release the member's `mtu 9216` must go (DERIVED)."""
    entry = delete_preview(serial, port)
    if not jumbo:
        e = entry["DATA"][0] if isinstance(entry.get("DATA"), list) else None
        target = e if e is not None else entry
        target["expectedConfig"] = without_mtu(target["expectedConfig"])
        target["pendingConfig"] = target["pendingConfig"] + ["  no mtu 9216"]
    return entry


def queue_delete(ctrl, jumbo=(True, True)):
    for (serial, port), j in zip(PEERS, jumbo):
        ctrl.vpc_previews[serial] = [released_delete_preview(serial, port, j)]


CANARY = "SYNTH-CANARY-Zq9"  # fake sensitive-looking value placed inside failing responses; it must never reach the error


def mutating(ctrl):
    return [(m, p) for m, p, _d in ctrl.calls if m in ("POST", "PUT", "DELETE")]


def lines(result):
    return [l.strip() for l in result.get("msg", "").splitlines() if l.startswith("  ")]


def refused(ctrl, items=None):
    status, result = run_vpc(ctrl, items or [vpc_item()])
    assert status == "fail", result
    assert mutating(ctrl) == [], mutating(ctrl)
    assert result["msg"].endswith("No configuration or deployment request was sent.")
    assert CANARY not in json.dumps(result)
    return lines(result)


class CanaryController(VpcController):
    """VpcController whose failing answers carry a fake canary in every place a careless diagnostic could copy from."""

    def __init__(self):
        super(CanaryController, self).__init__()
        self.canary_failures = set()

    def __call__(self, mod, method, path, data=None):
        for mark in self.canary_failures:
            if mark in path:
                self.calls.append((method, path, data))
                return {"RETURN_CODE": 500, "MESSAGE": CANARY, "DATA": {"message": CANARY, "detail": CANARY}}
        return super(CanaryController, self).__call__(mod, method, path, data)


def lo(ip, deploy=True):
    """A desired non-PVLAN interface, so the overridden request is not empty (the sweep keeps its normal scope)."""
    return {"name": "lo100", "type": "lo", "switch": [ip], "deploy": deploy,
            "profile": {"mode": "lo", "int_vrf": "", "ipv4_addr": "10.9.9.9", "admin_state": True}}


def with_args(harness, runner, ctrl, config, extra, **kw):
    """The harness runner with extra module arguments (global deploy, override_intf_types): the harness's own set_module_args is
    wrapped, nothing else changes."""
    original = harness.set_module_args
    with patch.object(harness, "set_module_args", side_effect=lambda a: original(dict(a, **extra))):
        return runner(ctrl, config, **kw)


def writes(ctrl):
    out = []
    for m, p, _d in ctrl.calls:
        if m in ("POST", "PUT", "DELETE") and "/config-preview" not in p and "networkAttachments" not in p:
            out.append(p.rsplit("/rest/", 1)[-1])
    return out


class MeasuredVpc(VpcController):
    """The vPC harness with the MEASURED summary `deletable` (child Po and physical members False, parent True)."""

    def _summary_entry(self, serial, name, d, status):
        entry = super(MeasuredVpc, self)._summary_entry(serial, name, d, status)
        if d["policy"] in (VPC_PO, PO_MEMBER, TRUNK, "int_access_host", "int_routed_host"):
            entry["deletable"] = "False"
        return entry


def measured_po(ctrl):
    """The Po harnesses report `deletable` True and no policy source on physical ports; the controller reports `deletable` False on a
    PVLAN member and on a standalone int_trunk_host, and the member's policy source is its port-channel in lower case (MEASURED in the
    summaries). The sweep then defers those ports to
    their source instead of resetting them directly, which is the path the controller really takes."""
    original = ctrl._summary_list

    def summary():
        out = original()
        for entry in out:
            if str(entry.get("isPhysical")).lower() == "true":
                entry["deletable"] = "False"
                d = ctrl.detail.get(entry["ifName"]) or {}
                if d.get("policy") == G4.PO_MEMBER:
                    for pol in entry.get("underlayPolicies") or []:
                        pol["source"] = str((d.get("nvPairs") or {}).get("PO_ID", "")).lower()
        return out

    ctrl._summary_list = summary
    return ctrl


def vpc_ctrl(cls=None):
    ctrl = (cls or MeasuredVpc)().seed_baseline().seed_vpc()
    ctrl.next_invocation()
    return ctrl


def vpc_queue(ctrl, n):
    for serial, port in ((SN1, M1), (SN2, M2)):
        ctrl.vpc_previews[serial] = [delete_preview(serial, port) for _i in range(n)]
