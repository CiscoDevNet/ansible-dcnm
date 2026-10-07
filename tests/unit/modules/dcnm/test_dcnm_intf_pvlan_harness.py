"""Harness for the native Ethernet PVLAN tests: real main(), external boundary mocked only.

Self-contained and collection-local. It mocks ONLY the external boundary -- inventory, version,
the transport (dcnm_send), the bulk-API probe, fabric details and sleep -- through a stateful,
path-routed fake controller that records every request in order. Nothing under test (builder,
reconciliation, preflight, pre-deploy gate) is stubbed. Fixtures come from
fixtures/dcnm_intf_pvlan_measured.json, sanitized from measured discovery evidence.

The fake controller APPLIES a successful modify to its stored intent, so later reads (post-deploy
readback, a second run) see what the module actually sent. Pending is NEVER computed by the fake:
each preview answer is a fixture or an explicit test value, so the gate is judged against data
it did not produce.

This file holds the harness plus its own sanity tests; it defines no product behavior.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

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

SERIAL = "SAL1819SAN8"
SWITCH_IP = "10.0.0.1"
FABRIC = "test_fabric"
IF7 = "Ethernet1/7"
IF8 = "Ethernet1/8"
PVLAN = "int_pvlan_host"
TRUNK = "int_trunk_host"
NDFC = "12.6.0.267"

FIXTURE = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "dcnm_intf_pvlan_measured.json")))
TRANSITIONS = dict((t["case"], t) for t in FIXTURE["transitions"])
# E2: measured device/controller authority (runningConfig / expectedConfig stanzas) per case.
DEVICE = json.load(open(os.path.join(os.path.dirname(__file__), "fixtures", "dcnm_intf_pvlan_device_measured.json")))["cases"]

PREVIEW_MARK = "/control/fabrics/{0}/config-preview/".format(FABRIC)
RECOMPUTE_FLAGS = "forceShowRun=true&showBrief=false&recomputeMapEnable=true&shRunOptimization=false"
MODIFY = "/rest/interface/modify"
DEPLOY = "/rest/globalInterface/deploy"
NETWORKS = "/top-down/fabrics/{0}/networks".format(FABRIC)
TEMPLATE = "/configtemplate/rest/config/templates/int_pvlan_host"
TEMPLATE_CONTENT = "##template variables\n" + FIXTURE["template_variables"] + "##template content\n"


def ok(data):
    return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": data}


def trunk_host_nv(ifname=IF7):
    nv = copy.deepcopy(FIXTURE["trunk_host_baseline"]["nvPairs"])
    nv["INTF_NAME"] = ifname
    return nv


def pvlan_nv(case_or_nv, ifname=IF7, which="post_nv"):
    """int_pvlan_host nvPairs: from a measured transition (its pre or post readback) or a dict."""
    nv = copy.deepcopy(TRANSITIONS[case_or_nv][which] if isinstance(case_or_nv, str) else case_or_nv)
    nv["INTF_NAME"] = ifname
    return nv


def pending(case, ifname=IF7):
    """Measured pending lines of a discovery transition, re-targeted to `ifname`."""
    lines = copy.deepcopy(TRANSITIONS[case]["pending"])
    return [l.replace("interface ethernet1/7", "interface " + ifname.lower()) for l in lines]


def preview(lines, serial=SERIAL, status=None, running=None, expected=None):
    """A legacy config-preview answer. `running`/`expected` are interface stanzas (header plus
    indented lines); without them the answer carries no device authority, as in E1."""
    if status is None:
        status = "Out-of-Sync" if lines else "In-Sync"
    entry = {"switchId": serial, "status": status, "pendingConfig": lines}
    if running is not None:
        entry["runningConfig"] = ["!Command: show running-config", "hostname placeholder-sw-1"] + list(running)
    if expected is not None:
        entry["expectedConfig"] = ["hostname placeholder-sw-1"] + list(expected)
    return ok([entry])


def _retarget(lines, ifname):
    return [l.replace("interface ethernet1/7", "interface " + ifname.lower()) for l in lines]


def authority(case, phase="pre", ifname=IF7):
    """(running_stanza, expected_stanza) measured for a discovery case and phase."""
    d = DEVICE[case][phase]
    return _retarget(d["running_stanza"], ifname), _retarget(d["expected_stanza"], ifname)


def measured_preview(case, phase="pre", ifname=IF7, serial=SERIAL):
    """The measured legacy preview of a discovery case: `pre` = after the intent write, before
    deploy; `post` = after the deploy (In-Sync, converged device)."""
    d = DEVICE[case][phase]
    running, expected = authority(case, phase, ifname)
    return preview(_retarget(d["pendingConfig"], ifname), serial=serial, status=d["status"], running=running, expected=expected)


DELETE = "__delete_key__"  # summary override value that removes the key from the entry


class FakeController(object):
    """Stateful NDFC double. Every request is appended to `calls` BEFORE it is answered."""

    def __init__(self):
        self.calls = []
        self.detail = {}  # ifName -> {"policy": str, "nvPairs": dict}
        self.summary = {}  # ifName -> overrides of the interface/detail entry
        self.summary_pre = {}  # ifName -> overrides applied only until the first deploy
        self.networks = copy.deepcopy(FIXTURE["networks"])
        self.template = ok({"name": PVLAN, "content": TEMPLATE_CONTENT})
        self.previews = []  # consumed in order; a callable gets (path) -> response
        self.modify_responses = []  # consumed in order; default: one SUCCESS item per interface
        self.deploy_responses = []  # consumed in order; default: measured success
        self.compliance = []  # consumed per summary read after a deploy; default In-Sync
        self.read_failures = set()  # path substrings answered with HTTP 500
        self.policies_extra = []  # additional live policies (for example an OVERLAY profile)
        self.policies_override = None  # replaces the whole policy-list answer when not None
        self.deployed = False
        # E4: the default summary entry has the MEASURED shape (no top-level `policy`, one nested
        # underlay object with the measured identity keys). True restores the earlier harness
        # shape's top-level `policy` (consistent with the underlay) for explicit controls.
        self.summary_top_policy = False
        # MODEL, not measured: the documented recomputeMapEnable effect (compliance recalculated)
        # is represented by aligning the summary status with the last preview served.
        self.recompute_status = None

    def next_invocation(self):
        """A new module invocation against the same controller: stored intent persists; the
        per-invocation recompute alignment and the deploy marker do not."""
        self.recompute_status = None
        self.deployed = False

    # ---- helpers for tests
    def requests(self, method=None, mark=None):
        return [c for c in self.calls if (method is None or c[0] == method) and (mark is None or mark in c[1])]

    def mutating(self):
        return [c for c in self.calls if c[0] in ("POST", "PUT", "DELETE") and "networkAttachments/query" not in c[1]]

    def manage(self):
        return [c for c in self.calls if "/api/v1/manage" in c[1] or "onemanage" in c[1].lower()]

    def modify_bodies(self):
        return [json.loads(c[2]) for c in self.requests("POST", MODIFY)]

    def sent_nv(self, ifname=IF7):
        found = None
        for body in self.modify_bodies():
            for payload in body:
                for intf in payload["interfaces"]:
                    if intf["ifName"] == ifname:
                        found = (payload["policy"], intf["nvPairs"])
        return found

    def order(self):
        out = []
        for c in self.calls:
            if PREVIEW_MARK in c[1]:
                out.append("PREVIEW")
            elif MODIFY in c[1]:
                out.append("MODIFY")
            elif DEPLOY in c[1]:
                out.append("DEPLOY")
        return out

    # ---- transport
    def __call__(self, mod, method, path, data=None):
        self.calls.append((method, path, data))
        for mark in self.read_failures:
            if mark in path:
                return {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}
        if path.endswith("/accessmode"):
            return ok({"readonly": False})
        if PREVIEW_MARK in path:
            nxt = self.previews.pop(0) if self.previews else preview([])
            nxt = nxt(path) if callable(nxt) else nxt
            entries = nxt.get("DATA") if isinstance(nxt, dict) else None
            if isinstance(entries, list) and entries and isinstance(entries[0], dict) and entries[0].get("status") in ("In-Sync", "Out-of-Sync"):
                self.recompute_status = (entries[0]["status"], self.deployed)
            return nxt
        if path.endswith(TEMPLATE):
            return self.template
        if path.endswith(NETWORKS):
            return ok(copy.deepcopy(self.networks))
        if "/control/policies/switches/" in path:
            if self.policies_override is not None:
                return copy.deepcopy(self.policies_override)
            return ok(self._policies())
        if "/rest/interface/detail?serialNumber=" in path:
            return ok(self._summary_list())
        if "/rest/interface?serialNumber=" in path:
            if "&ifName=" in path:
                name = path.split("&ifName=")[1]
                d = self.detail.get(name)
                return ok([self._detail_entry(name, d)] if d else [])
            return ok([self._detail_entry(n, d) for n, d in sorted(self.detail.items())])
        if method == "POST" and path.endswith(MODIFY):
            body = json.loads(data)
            resp = self.modify_responses.pop(0) if self.modify_responses else None
            if resp is None:
                items = []
                for payload in body:
                    for intf in payload["interfaces"]:
                        items.append(
                            {
                                "reportItemType": "SUCCESS",
                                "message": "Interface updated successfully",
                                "entity": "%s~%s" % (intf["serialNumber"], intf["ifName"]),
                            }
                        )
                resp = {"RETURN_CODE": 207, "MESSAGE": "Multi-Status", "DATA": items}
            data = resp.get("DATA")
            if isinstance(data, list) and data and all(isinstance(i, dict) and str(i.get("reportItemType")).upper() == "SUCCESS" for i in data):
                for payload in body:
                    for intf in payload["interfaces"]:
                        self.detail[intf["ifName"]] = {"policy": payload["policy"], "nvPairs": copy.deepcopy(intf["nvPairs"])}
            return resp
        if method == "POST" and path.endswith(DEPLOY):
            self.deployed = True
            if self.deploy_responses:
                return self.deploy_responses.pop(0)
            # The MEASURED success shape (one interface, G5/G6), generalized here to name every
            # requested interface. Naming several in one body is NOT measured.
            body = json.loads(data)
            body = body if isinstance(body, list) else [body]
            return ok({"message": FIXTURE["deploy_success"]["message"], "value": [{"serialNumber": i["serialNumber"], "IfName": i["ifName"]} for i in body]})
        return ok({})

    def _detail_entry(self, name, d):
        return {"policy": d["policy"], "interfaces": [{"serialNumber": SERIAL, "ifName": name, "nvPairs": copy.deepcopy(d["nvPairs"])}]}

    @staticmethod
    def _policy_id(index):
        return "POLICY-%d" % (100 + index)

    def _policies(self):
        out = []
        for index, (name, d) in enumerate(sorted(self.detail.items())):
            out.append(
                {
                    "entityName": name,
                    "entityType": "INTERFACE",
                    "templateName": d["policy"],
                    "source": "",
                    "deleted": False,
                    "policyId": self._policy_id(index),
                    "priority": 500,
                    "serialNumber": SERIAL,
                    "autoGenerated": True,
                }
            )
        return out + copy.deepcopy(self.policies_extra)

    def _summary_list(self):
        out = []
        status = self.compliance.pop(0) if (self.deployed and self.compliance) else "In-Sync"
        for index, (name, d) in enumerate(sorted(self.detail.items())):
            entry = {
                "ifName": name,
                "serialNo": SERIAL,
                "fabricName": FABRIC,
                "ifType": "INTERFACE_ETHERNET",
                "isPhysical": "True",
                "deletable": "True",
                "editAllowed": "True",
                "markDeleted": "False",
                "alias": "",
                "deleteReason": None,
                "complianceStatus": status,
                "mode": "trunk",
                # MEASURED keys of the nested object (LQA1-OBSERVE, NDFC 12.6.0.267); values follow
                # this fake's own detail and policy list.
                "underlayPolicies": [
                    {
                        "source": "",
                        "templateName": d["policy"],
                        "policyId": self._policy_id(index),
                        "entityName": name,
                        "entityType": "INTERFACE",
                        "serialNumber": SERIAL,
                    }
                ],
                "interfaces": [{"nvPairs": {}}],
            }
            if self.summary_top_policy:
                entry["policy"] = d["policy"]
            entry.update(copy.deepcopy(self.summary.get(name, {})))
            if not self.deployed:
                entry.update(copy.deepcopy(self.summary_pre.get(name, {})))
                if self.recompute_status and self.recompute_status[0] == "In-Sync":
                    entry["complianceStatus"] = "In-Sync"
            for key in [k for k, v in entry.items() if v == DELETE]:
                entry.pop(key)
            out.append(entry)
        return out


def pvlan_item(ifname=IF7, deploy=True, **profile):
    prof = {"mode": "pvlan"}
    prof.update(profile)
    return {"name": ifname, "type": "eth", "switch": [SWITCH_IP], "deploy": deploy, "profile": prof}


def trunk_item(ifname=IF8, deploy=True, **profile):
    prof = {"mode": "trunk"}
    prof.update(profile)
    return {"name": ifname, "type": "eth", "switch": [SWITCH_IP], "deploy": deploy, "profile": prof}


INVENTORY = {
    SWITCH_IP: {
        "logicalName": "placeholder-sw-1",
        "serialNumber": SERIAL,
        "isVpcConfigured": "False",
        "vpcDomain": 0,
        "switchRole": "leaf",
        "managable": "True",
    }
}


def run(ctrl, config, state="merged", check_mode=False, check_deploy=False, bulk=True, version=(12, NDFC),
        patch_version=None):
    """Drive the real main(). Returns ("exit"|"fail", result dict).

    patch_version is omitted from module args unless given: native PVLAN needs no patch context,
    so every case here exercises it with the argument genuinely absent by default.
    """
    args = {"state": state, "fabric": FABRIC, "config": config, "check_deploy": check_deploy}
    if patch_version is not None:
        args["patch_version"] = patch_version
    if check_mode:
        args["_ansible_check_mode"] = True
    patches = [
        patch.object(basic.AnsibleModule, "exit_json", exit_json),
        patch.object(basic.AnsibleModule, "fail_json", fail_json),
        patch.object(module, "get_fabric_inventory_details", return_value=copy.deepcopy(INVENTORY)),
        patch.object(module, "get_ip_sn_dict", return_value=({SWITCH_IP: SERIAL}, {})),
        patch.object(module, "dcnm_get_ip_addr_info", side_effect=lambda m, sw, a, b: sw),
        patch.object(module, "dcnm_version_supported", return_value=version),
        patch.object(module, "dcnm_send", side_effect=ctrl),
        patch.object(module, "dcnm_get_bulk_api_support", return_value=bulk),
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


# ---------------------------------------------------------------- harness self-tests
def test_harness_fixture_is_sanitized_and_complete():
    raw = json.dumps(FIXTURE)
    for leaked in ("9648E3J5P6M", "FAB1", "Leaf-101", "192.168.", "POLICY-"):
        assert leaked not in raw
    assert {"TU2", "TX1", "TX2", "PU3", "G6-M1", "G6-L1", "G6-MR"} <= set(TRANSITIONS)
    assert "MAPPING_LIST[]" in FIXTURE["template_variables"]


def test_harness_records_before_answering_and_never_computes_pending():
    ctrl = FakeController()
    assert ctrl(None, "GET", "/x" + PREVIEW_MARK + SERIAL + "?" + RECOMPUTE_FLAGS) == preview([])
    assert ctrl.calls[0][0] == "GET" and ctrl.order() == ["PREVIEW"]


# ---------------------------------------------------------------- E2: module reset (TEMPLATE-PREDICTED)
# NOT MEASURED. The module's Ethernet default reset (dcnm_intf_get_default_eth_payload) sends
# BPDUGUARD_ENABLED=false; the installed int_trunk_host add() (sha256 99dc8f0a...) renders
# 'spanning-tree bpduguard disable' for that value. The measured G6-MR read is an EXACT
# restoration whose BPDUGUARD was 'no', so it is not the module reset. These helpers add exactly
# that one template-derived line to the measured G6-MR / G6-M0a data and nothing else.
BPDU_DISABLE = "  spanning-tree bpduguard disable"


def _insert_before_end(lines, extra):
    out = list(lines)
    index = out.index("configure terminal") if "configure terminal" in out else len(out)
    return out[:index] + list(extra) + out[index:]


def reset_preview(ifname=IF7, serial=SERIAL):
    """Predicted pre-deploy preview of a PVLAN -> module Ethernet default reset."""
    d = DEVICE["G6-MR"]["pre"]
    running, expected = authority("G6-MR", "pre", ifname)
    lines = _insert_before_end(_retarget(d["pendingConfig"], ifname), [BPDU_DISABLE])
    return preview(lines, serial=serial, status="Out-of-Sync", running=running, expected=expected + [BPDU_DISABLE])


def reset_device_stanza(ifname=IF7):
    """Predicted device stanza after the module reset converged (measured G6-MR post + the line)."""
    return authority("G6-MR", "post", ifname)[0] + [BPDU_DISABLE]


def recreate_preview(ifname=IF7, serial=SERIAL):
    """Predicted preview of trunk promiscuous 2210/2211 over a module-reset port: the measured
    G6-M0a conversion plus the withdrawal of the predicted bpduguard line."""
    d = DEVICE["G6-M0a"]["pre"]
    lines = _retarget(d["pendingConfig"], ifname)
    index = lines.index("  no switchport mode trunk") + 1
    lines = lines[:index] + ["  no spanning-tree bpduguard disable"] + lines[index:]
    return preview(lines, serial=serial, status="Out-of-Sync", running=reset_device_stanza(ifname), expected=authority("G6-M0a", "pre", ifname)[1])
