"""Port-channel PVLAN controller doubles, previews and stanzas shared by the port-channel suites."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from .ethernet_controller import IF7, SERIAL, SWITCH_IP, TRUNK, FakeController, ok, preview, run, trunk_host_nv
from .fixture_cases import load_case


PO = "Port-channel10"  # the module-normalised name; device stanzas stay lower case
PO_ITEM_NAME = "po10"
PO_HOST = "int_port_channel_pvlan_host"
PO_MEMBER = "int_port_channel_pvlan_member"
GLOBAL_IF = "/rest/globalInterface"
DEPLOY = "/rest/globalInterface/deploy"
MODIFY = "/rest/interface/modify"
PRIMARY, SECONDARY = 2210, 2212  # candidates, not validated by this review

RUNNING_MEMBER = ["interface Ethernet1/7", "  switchport", "  switchport mode trunk",
                  "  switchport trunk allowed vlan none", "  spanning-tree port type edge trunk",
                  "  mtu 9216", "  shutdown"]
PO_STANZA = ["interface port-channel10", "  switchport", "  switchport mode private-vlan host",
             "  switchport private-vlan host-association 2210 2212", "  mtu 9216",
             "  spanning-tree bpduguard enable", "  spanning-tree port type edge trunk", "  shutdown"]
# MEASURED member forms of the creation (fixtures/pvlan_po_create_update.json#pvlan_po_h1_measured, port-channel502 /
# Ethernet1/10), TRANSPOSED to this harness's names (port-channel10 / Ethernet1/7). The controller's expected member holds
# `channel-group N mode active` (no `force`) plus the inherited PVLAN mode and list line; the member pending holds only
# `no spanning-tree port type edge trunk` (before the parent block) and `channel-group N force mode active` + `shutdown`.
# The G1/E2 hand predictions (expected WITH force; pending withdrawing the trunk lines and adding the PVLAN lines) were
# contradicted by that measurement.
MEMBER_AFTER = ["interface ethernet1/7", "  channel-group 10 mode active", "  mtu 9216", "  shutdown", "  switchport",
                "  switchport mode private-vlan host", "  switchport private-vlan host-association 2210 2212"]
PENDING_NEW = (["interface ethernet1/7", "  no spanning-tree port type edge trunk"] + PO_STANZA
               + ["interface ethernet1/7", "  channel-group 10 force mode active", "  shutdown", "configure terminal"])


class PoController(FakeController):
    """The existing fake controller + the port-channel create path (POST globalInterface)."""

    def __init__(self):
        super(PoController, self).__init__()
        self.create_responses = []
        self.po_names = set()

    def __call__(self, mod, method, path, data=None):
        if method == "POST" and path.endswith(GLOBAL_IF):
            self.calls.append((method, path, data))
            resp = self.create_responses.pop(0) if self.create_responses else ok({})
            body = json.loads(data)
            body = body if isinstance(body, list) else [body]
            if resp.get("RETURN_CODE") in (200, 207):
                for payload in body:
                    for intf in payload["interfaces"]:
                        self.detail[intf["ifName"]] = {"policy": payload["policy"], "nvPairs": copy.deepcopy(intf["nvPairs"])}
                        self.po_names.add(intf["ifName"])
            return resp
        return super(PoController, self).__call__(mod, method, path, data)

    def _summary_list(self):
        out = super(PoController, self)._summary_list()
        for entry in out:
            if entry["ifName"] in self.po_names:
                entry["ifType"], entry["isPhysical"], entry["mode"] = "INTERFACE_PORT_CHANNEL", "False", "trunk"
        return out

    def creates(self):
        return [c for c in self.calls if c[0] == "POST" and c[1].endswith(GLOBAL_IF)]

    def deploys(self):
        return [c for c in self.calls if c[0] == "POST" and c[1].endswith(DEPLOY)]

    def writes(self):
        return [c for c in self.calls if c[0] in ("POST", "PUT", "DELETE") and "networkAttachments/query" not in c[1]
                and "/config-preview" not in c[1]]


def _as_list(body):
    return body if isinstance(body, list) else [body]


def po_item(name=PO_ITEM_NAME, deploy=True, **profile):
    prof = {"mode": "pvlan", "pvlan_mode": "host", "members": [IF7], "admin_state": False,
            "pvlan_association": [{"primary_vlan": PRIMARY, "secondary_vlan": SECONDARY}]}
    prof.update(profile)
    return {"name": name, "type": "pc", "switch": [SWITCH_IP], "deploy": deploy, "profile": prof}


def baseline_ctrl(member_nv=None):
    ctrl = PoController()
    ctrl.detail[IF7] = {"policy": TRUNK, "nvPairs": member_nv if member_nv is not None else trunk_host_nv(IF7)}
    return ctrl


def good_preview():
    return preview(PENDING_NEW, running=RUNNING_MEMBER, expected=PO_STANZA + MEMBER_AFTER)


def created_ctrl():
    """Controller state after a successful M1 (SYNTHETIC: the member policy flip is predicted)."""
    ctrl = baseline_ctrl()
    ctrl.previews = [good_preview()]
    status, result = run(ctrl, [po_item()])
    assert status == "exit", result
    nv = {"PO_ID": PO, "PC_MODE": "active", "PVLAN_MODE": "host", "CDP_ENABLE": "true", "lldpTransmit": "false",
          "lldpReceive": "false", "LACP_PORT_PRIO": "32768", "LACP_RATE": "normal", "DESC": "", "CONF": "",
          "ADMIN_STATE": "false", "INTF_NAME": IF7}
    ctrl.detail[IF7] = {"policy": PO_MEMBER, "nvPairs": nv}
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl


# ------------------------------------------------------------------ existing routes that could reach a PVLAN Po/member
# Found by probing the existing routes: before the guard these four reached the
# controller (markdelete / modify / deploy). Each is now refused before any write.
def _eth(name, mode="trunk"):
    return {"name": name, "type": "eth", "switch": [SWITCH_IP], "deploy": False, "profile": {"mode": mode}}


MARKDELETE = "/rest/interface/markdelete"
BULK = "/rest/interface/modify"


def markdelete_ok(data):
    """The MEASURED mark-delete success answer (wire log, NDFC 12.6.0.267): 200/OK with DATA.message and one
    `value` item per deleted interface naming its serial and IfName."""
    body = json.loads(data)
    body = body if isinstance(body, list) else [body]
    return ok(
        {
            "message": "Interface deleted successfully",
            "value": [{"interfaceType": "INTERFACE_PORT_CHANNEL", "serialNumber": i.get("serialNumber"), "IfName": i.get("ifName")} for i in body],
        }
    )


class PoLifecycleController(PoController):
    """PoController + a markdelete that removes the parent and leaves the member on the released trunk policy (the
    measured regular-Po behaviour; for a PVLAN member this is the PREDICTION under test, not a measurement)."""

    def __init__(self):
        super(PoLifecycleController, self).__init__()
        self.release_member = True
        self.inherited_child = True

    def __call__(self, mod, method, path, data=None):
        if method == "DELETE" and path.endswith(MARKDELETE):
            self.calls.append((method, path, data))
            body = json.loads(data)
            for intf in body if isinstance(body, list) else [body]:
                name = intf.get("ifName")
                parent = self.detail.pop(name, None)
                self.po_names.discard(name)
                if parent and self.release_member:
                    for member in str(parent["nvPairs"].get("MEMBER_INTERFACES", "")).split(","):
                        if member.strip():
                            nv = trunk_host_nv(member.strip())
                            nv["ADMIN_STATE"] = "false"
                            self.detail[member.strip()] = {"policy": TRUNK, "nvPairs": nv}
            return markdelete_ok(data)
        return super(PoLifecycleController, self).__call__(mod, method, path, data)

    def _policies(self):
        """The member policies in the MEASURED shape (fixtures/pvlan_po_create_update.json#pvlan_po_h1_measured): the
        int_port_channel_pvlan_member carries the port-channel as source, and the parent's 'Inherited Commands' int_eth
        child (source = the port-channel) sits on the same member. The base harness gives every policy source ''."""
        out = super(PoLifecycleController, self)._policies()
        children = []
        for p in out:
            if p["templateName"] == PO_MEMBER:
                po = str(self.detail[p["entityName"]]["nvPairs"].get("PO_ID", "")).lower()
                p["source"] = po
                if self.inherited_child:
                    children.append(
                        dict(p, templateName="int_eth", source=po, policyId=p["policyId"] + "-inherited", priority=512, description="Inherited Commands")
                    )
        return out + children

    def bulk_bodies(self):
        return [json.loads(c[2]) for c in self.calls if c[0] == "POST" and c[1].endswith(BULK)]

    def markdeletes(self):
        return [c for c in self.calls if c[0] == "DELETE" and c[1].endswith(MARKDELETE)]


def item(mode, deploy=True, **profile):
    prof = {"mode": "pvlan", "pvlan_mode": mode, "members": [IF7], "admin_state": False}
    prof.update(profile)
    return {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": deploy, "profile": prof}


def po_stanza(mode, lines):
    return (
        ["interface port-channel10", "  switchport", "  switchport mode private-vlan %s" % mode]
        + ["  " + l for l in lines]
        + ["  mtu 9216", "  spanning-tree bpduguard enable", "  spanning-tree port type edge trunk", "  shutdown"]
    )


def member_stanza(mode, lines):
    # The MEASURED expected member form (host), transposed: persisted `channel-group N mode active` (no force) and
    # the parent's PVLAN mode/list lines. For the other modes this is the same form, NOT measured (SYNTHETIC, inferred).
    return [
        "interface ethernet1/7",
        "  channel-group 10 mode active",
        "  mtu 9216",
        "  shutdown",
        "  switchport",
        "  switchport mode private-vlan %s" % mode,
    ] + ["  " + l for l in lines]


# Trunk secondary is created only from a member PREPARED as access (or routed); it was MEASURED that a switchport-trunk member
# is rejected by the device. The prepared access member is the measured access-branch one (fixtures/pvlan_po_delete_saved.json#pvlan_po_ts_exp1_measured).
EXP1 = load_case("pvlan_po_ts_exp1_measured")
ACCESS = "int_access_host"
RUNNING_ACCESS = ["interface Ethernet1/7", "  shutdown", "  spanning-tree port type edge", "  mtu 9216"]


def prepared_access_nv(ifname=IF7):
    nv = dict((k, v) for k, v in EXP1["branches"]["A"]["member_before"]["intent"]["Ethernet1/8"]["nvPairs"].items() if k != "POLICY_ID")
    nv["INTF_NAME"] = ifname
    return nv


def create_preview(mode, lines):
    # The MEASURED pending form of a member creation (host), transposed: the trunk spanning-tree withdrawal before
    # the parent block, then `channel-group N force mode active` + `shutdown`. For promiscuous and trunk promiscuous this form
    # is now MEASURED (P1, TP1); trunk secondary uses the MEASURED access-member form (`no spanning-tree port type
    # edge`), transposed to the harness port-channel10/Ethernet1/7.
    ts = mode == "trunk secondary"
    pend = (
        ["interface ethernet1/7", "  no spanning-tree port type edge" if ts else "  no spanning-tree port type edge trunk"]
        + po_stanza(mode, lines)
        + ["interface ethernet1/7", "  channel-group 10 force mode active", "  shutdown", "configure terminal"]
    )
    return preview(pend, running=RUNNING_ACCESS if ts else RUNNING_MEMBER, expected=po_stanza(mode, lines) + member_stanza(mode, lines))


def baseline(mode=None):
    ctrl = PoLifecycleController()
    if mode == "trunk secondary":
        ctrl.detail[IF7] = {"policy": ACCESS, "nvPairs": prepared_access_nv(IF7)}
    else:
        ctrl.detail[IF7] = {"policy": TRUNK, "nvPairs": trunk_host_nv(IF7)}
    return ctrl


def created(mode, lines, **profile):
    """Controller holding an EXISTING port-channel of `mode` with its member (SYNTHETIC member flip, as in
    created_ctrl). Every mode is created through main() (host: measured force form; the others: inferred, with the
    synthetic create_preview)."""
    ctrl = baseline(mode)
    ctrl.previews = [create_preview(mode, lines)]
    status, result = run(ctrl, [item(mode, **profile)], state="replaced")
    assert status == "exit" and result["changed"] is True, result
    parent = ctrl.detail[PO]["nvPairs"]
    ctrl.detail[IF7] = {
        "policy": PO_MEMBER,
        "nvPairs": {
            "PO_ID": PO,
            "PC_MODE": "active",
            "PVLAN_MODE": mode,
            "CDP_ENABLE": "true",
            "lldpTransmit": "false",
            "lldpReceive": "false",
            "LACP_PORT_PRIO": "32768",
            "LACP_RATE": "normal",
            "DESC": "",
            "CONF": "",
            "ADMIN_STATE": "false",
            "INTF_NAME": IF7,
        },
    }
    assert parent["PVLAN_MODE"] == mode
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl


# ------------------------------------------------------------------ PO-PR: deletion of the own port-channel
def delete_preview(mode, lines):
    run_cfg = po_stanza(mode, lines) + member_stanza(mode, lines)
    released = [
        "interface Ethernet1/7",
        "  switchport",
        "  switchport mode trunk",
        "  switchport trunk allowed vlan none",
        "  spanning-tree port type edge trunk",
        "  mtu 9216",
        "  shutdown",
    ]
    pend = (
        ["no interface port-channel10", "interface Ethernet1/7", "  no switchport mode private-vlan %s" % mode]
        + ["  no " + l for l in lines]
        # The running member holds the PERSISTED `channel-group 10 mode active` (measured form), so the synthetic
        # withdrawal names that line. The deletion pending of a DEPLOYED PVLAN port-channel is NOT MEASURED (deleted a
        # never-deployed one); this stays a synthetic prediction.
        + ["  no channel-group 10 mode active", "  switchport mode trunk", "  switchport trunk allowed vlan none", "  spanning-tree port type edge trunk"]
    )
    return preview(pend, running=run_cfg, expected=released)


def del_item(**profile):
    out = {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True}
    if profile:
        out["profile"] = profile
    return out


NATIVE = "switchport private-vlan trunk native vlan 2301"
ALLOWED = "switchport private-vlan trunk allowed vlan 2301"

# Battery profiles (creation) and their synthetic expected list lines.
CASES = {
    "promiscuous": (
        {"pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2212"}]},
        ["switchport private-vlan mapping 2210 2212"],
    ),
    "trunk promiscuous": (
        {
            "pvlan_mapping": [{"primary_vlan": 2210, "secondary_vlans": "2211-2212"}, {"primary_vlan": 2410, "secondary_vlans": "2412"}],
            "native_vlan": "2301",
            "allowed_vlans": "2301",
        },
        [
            NATIVE,
            ALLOWED,
            "switchport private-vlan mapping trunk 2210 2211",
            "switchport private-vlan mapping trunk 2210 2212",
            "switchport private-vlan mapping trunk 2410 2412",
        ],
    ),
    "trunk secondary": (
        {
            "pvlan_association": [{"primary_vlan": 2210, "secondary_vlan": 2212}, {"primary_vlan": 2410, "secondary_vlan": 2412}],
            "native_vlan": "2301",
            "allowed_vlans": "2301",
        },
        [NATIVE, ALLOWED, "switchport private-vlan association trunk 2210 2212", "switchport private-vlan association trunk 2410 2412"],
    ),
}
MODES = sorted(CASES)


def with_second_primary(ctrl):
    """SYNTHETIC networks for the battery's second primary: 2410 primary, 2412 isolated (copied shapes of the fixture)."""
    nets = ctrl.networks
    prim = copy.deepcopy([n for n in nets if n["type"] == "Primary"][0])
    iso = copy.deepcopy([n for n in nets if n["type"] == "Isolated"][0])
    prim.update(networkId=30410, networkName="SYN_PRIMARY_2410", networkTemplateConfig=prim["networkTemplateConfig"].replace("2210", "2410"))
    iso.update(
        networkId=30412,
        networkName="SYN_ISOLATED_2412",
        primaryNetworkId=30410,
        networkTemplateConfig=iso["networkTemplateConfig"].replace("2212", "2412"),
    )
    nets += [prim, iso]
    return ctrl


def new_ctrl(mode=None):
    return with_second_primary(baseline(mode))


def creation_preview(mode, lines, pending_member=None, expected_member=None, extra=()):
    """The synthetic creation preview of g1 (measured host form transposed) with an optional named change."""
    pv = create_preview(mode, lines)
    entry = pv["DATA"][0]
    if pending_member is not None:
        pend = entry["pendingConfig"]
        start = len(pend) - 1 - pend[::-1].index("interface ethernet1/7")
        entry["pendingConfig"] = pend[: start + 1] + ["  " + l for l in pending_member] + ["configure terminal"]
    if expected_member is not None:
        entry["expectedConfig"] = ["hostname placeholder-sw-1"] + po_stanza(mode, lines) + expected_member
    if extra:
        entry["pendingConfig"] = entry["pendingConfig"][:-1] + list(extra) + ["configure terminal"]
    return pv


def create(mode, ctrl=None, pv=None):
    profile, lines = CASES[mode]
    ctrl = ctrl or new_ctrl(mode)
    ctrl.previews = [pv or creation_preview(mode, lines)]
    status, result = run(ctrl, [item(mode, **profile)], state="replaced")
    return ctrl, status, result


def existing(mode):
    """A port-channel of `mode` created through main() with the battery profile, then the SYNTHETIC member flip of the g1
    helper (the controller rewriting the member as int_port_channel_pvlan_member)."""
    ctrl, status, result = create(mode)
    assert status == "exit", result.get("msg")
    ctrl.detail[IF7] = {
        "policy": PO_MEMBER,
        "nvPairs": {
            "PO_ID": PO,
            "PC_MODE": "active",
            "PVLAN_MODE": mode,
            "CDP_ENABLE": "true",
            "lldpTransmit": "false",
            "lldpReceive": "false",
            "LACP_PORT_PRIO": "32768",
            "LACP_RATE": "normal",
            "DESC": "",
            "CONF": "",
            "ADMIN_STATE": "false",
            "INTF_NAME": IF7,
        },
    }
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl


# ================================================================== live host findings
# MEASURED (fixtures/pvlan_po_create_update.json#pvlan_po_g4r1_host_measured, extracted read-only from the G4R1 live captures;
# only port-channel502 / Ethernet1/10): H4 (host association 2210/2212 -> 2410/2412 on a
# deployed Po: member pending EMPTY) and the R-B deletion of that DEPLOYED Po (Po listed as interface_delete until the
# deploy; member withdrawn with `no channel-group 502 force mode active`; released member ADMIN_STATE "true").
# SIMULATED: the networks 2410/2412 typing, the legacy modify answer, and the post-correction deletion preview (named below).
G4R1 = load_case("pvlan_po_g4r1_host_measured")
PO_NAME_502, PO_502, MEM_10 = "port-channel502", "Port-channel502", "Ethernet1/10"


def g4r1_stage(name):
    return copy.deepcopy(G4R1["stages"][name])


def g4r1_entry(name, pending=None, expected=None, running=None):
    pf = g4r1_stage(name)["preview_forced"]
    return preview(
        pending if pending is not None else pf["pendingConfig"],
        running=running if running is not None else pf["runningConfig_stanzas"],
        expected=expected if expected is not None else pf["expectedConfig_stanzas"],
    )["DATA"][0]


class DeployedReleaseController(PoLifecycleController):
    """The g1 lifecycle harness + the MEASURED release of a DEPLOYED port-channel: after the mark-delete the
    Po's detail is empty, its summary entry stays (markDeleted, NA, interface_delete) and the policy list holds the
    interface_delete (deleted true) until the deploy; the member is the measured released int_trunk_host (ADMIN "true")."""

    def __init__(self, marked_entry=None):
        super(DeployedReleaseController, self).__init__()
        self.release_member = False
        po_summary = [x for x in g4r1_stage("HR-post")["summary"] if x["ifName"] == PO_502][0]
        po_summary["serialNo"] = SERIAL
        po_summary["underlayPolicies"][0]["serialNumber"] = SERIAL
        po_summary.update(marked_entry or {})
        self.marked_template = po_summary
        self.marked = None
        self.released = dict((k, v) for k, v in g4r1_stage("HR-post")["intent"][MEM_10]["nvPairs"].items() if k != "POLICY_ID")

    def __call__(self, mod, method, path, data=None):
        if method == "DELETE" and path.endswith("/rest/interface/markdelete"):
            resp = super(DeployedReleaseController, self).__call__(mod, method, path, data)
            self.detail[MEM_10] = {"policy": TRUNK, "nvPairs": copy.deepcopy(self.released)}
            self.marked = copy.deepcopy(self.marked_template)
            self.policies_extra = [dict(p, serialNumber=SERIAL) for p in g4r1_stage("HR-post")["policies"] if p["templateName"] == "interface_delete"]
            return resp
        resp = super(DeployedReleaseController, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith("/rest/globalInterface/deploy"):
            self.marked, self.policies_extra = None, []  # the deploy completes the deletion (NOT measured for a deployed Po)
        return resp

    def _summary_list(self):
        return super(DeployedReleaseController, self)._summary_list() + ([copy.deepcopy(self.marked)] if self.marked else [])

    def modifies(self):
        return [c for c in self.calls if c[0] == "POST" and c[1].endswith("/rest/interface/modify")]


def hr_ctrl(previews, **marked):
    ctrl = DeployedReleaseController(marked or None)
    for name, key in ((PO_502, PO_NAME_502), (MEM_10, MEM_10)):
        nv = dict((k, v) for k, v in g4r1_stage("HR-pre")["intent"][key]["nvPairs"].items() if k != "POLICY_ID")
        ctrl.detail[name] = {"policy": g4r1_stage("HR-pre")["intent"][key]["policy"], "nvPairs": nv}
    ctrl.po_names.add(PO_502)
    ctrl.previews = previews
    return ctrl


def corrected_hr_preview():
    """SYNTHETIC, one named change of the MEASURED HR-post entry: the member corrected to ADMIN_STATE false, so the
    controller's expected member holds `shutdown` and the pending no longer carries `no shutdown` (the post-correction
    pending of a DEPLOYED Po is NOT measured; for the never-deployed Po the measured correction gave In-Sync)."""
    pf = g4r1_stage("HR-post")["preview_forced"]
    pending = [l for l in pf["pendingConfig"] if l != "  no shutdown"]
    expected = ["  shutdown" if l == "  no shutdown" else l for l in pf["expectedConfig_stanzas"]]
    return {"RETURN_CODE": 200, "MESSAGE": "OK", "DATA": [g4r1_entry("HR-post", pending=pending, expected=expected)]}


def hr_delete(ctrl):
    return run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")


FF_A = "logging event port link-status"
FF_B = "no snmp trap link-status"
HOST_LINES = ["switchport private-vlan host-association 2210 2212"]
ASSOC = [{"primary_vlan": 2210, "secondary_vlan": 2212}]


def created_with(po_extra, member_extra, **profile):
    """An EXISTING host port-channel created through main() with RC1 fields: the po_g1 creation shape plus the extra Po / member lines
    (SYNTHETIC, template-predicted), then the member flip of po_g1.created()."""
    ctrl = baseline("host")
    po = po_stanza("host", HOST_LINES) + ["  " + x for x in po_extra]
    member = member_stanza("host", HOST_LINES) + ["  " + x for x in member_extra]
    pend = (["interface ethernet1/7", "  no spanning-tree port type edge trunk"] + po
            + ["interface ethernet1/7", "  channel-group 10 force mode active", "  shutdown"]
            + ["  " + x for x in member_extra] + ["configure terminal"])
    ctrl.previews = [preview(pend, running=RUNNING_MEMBER, expected=po + member)]
    status, result = run(ctrl, [item("host", pvlan_association=ASSOC, **profile)], state="replaced")
    assert status == "exit" and result["changed"] is True, result.get("msg")
    body = json.loads(ctrl.creates()[0][2])
    result["created_nv"] = (body[0] if isinstance(body, list) else body)["interfaces"][0]["nvPairs"]
    ctrl.detail[IF7] = {"policy": PO_MEMBER, "nvPairs": {
        "PO_ID": PO, "PC_MODE": "active", "PVLAN_MODE": "host", "CDP_ENABLE": "true", "lldpTransmit": "false", "lldpReceive": "false",
        "LACP_PORT_PRIO": "32768", "LACP_RATE": "normal", "DESC": "", "CONF": "", "ADMIN_STATE": "false", "INTF_NAME": IF7}}
    ctrl.next_invocation()
    ctrl.calls = []
    return ctrl, result
