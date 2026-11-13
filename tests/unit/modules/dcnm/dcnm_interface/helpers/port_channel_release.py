"""Shared test helpers."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from ansible_collections.cisco.dcnm.plugins.module_utils import interface_pvlan as P
from .ethernet_controller import SWITCH_IP, TRUNK, preview, run
from .port_channel_controller import PoLifecycleController, markdelete_ok
from .fixture_cases import load_case


FIXTURE = load_case("pvlan_po_h1_measured")
PO_NAME, MEM = "port-channel502", "Ethernet1/10"
PO = "Port-channel502"
PO_MEMBER = "int_port_channel_pvlan_member"
MARKDELETE = "/rest/interface/markdelete"
MODIFY = "/rest/interface/modify"
DEPLOY = "/rest/globalInterface/deploy"
SUMMARY = "/rest/interface/detail?serialNumber="
POLICIES = "/control/policies/switches/"
DETAIL = "/rest/interface?serialNumber="
ERROR = {"RETURN_CODE": 500, "MESSAGE": "Internal Server Error", "DATA": {}}


def stage(name):
    return copy.deepcopy(FIXTURE["stages"][name])


def harness_nv(nv):
    """Measured nvPairs for the harness: only POLICY_ID dropped (the harness numbers its own policies)."""
    return dict((k, v) for k, v in nv.items() if k != "POLICY_ID")


def entry(name):
    pf = stage(name)["preview_forced"]
    return {
        "RETURN_CODE": 200,
        "MESSAGE": "OK",
        "DATA": [preview(pf["pendingConfig"], running=pf["runningConfig_stanzas"], expected=pf["expectedConfig_stanzas"])["DATA"][0]],
    }


RELEASED = harness_nv(stage("HR-post")["intent"][MEM]["nvPairs"])  # MEASURED: int_trunk_host, ADMIN_STATE "true"


class ReleaseController(PoLifecycleController):
    """The existing Po harness + the MEASURED release: the mark-delete removes the parent and its member policies and
    leaves the member as `released_nv` (default: the measured HR-post int_trunk_host, ADMIN_STATE "true").

    Knobs, all after the mark-delete: `fail_after_delete` = path markers answered 500; `extra_after_delete` = live
    policies that appear; `released_policy` = the member's template; `keep_parent`; `modify_mode` in
    {"store" (default harness: 207 SUCCESS, store the sent nvPairs), "lossy" (store but lose/alter a field),
    "keep_up" (answer SUCCESS but leave ADMIN_STATE "true")}; `modify_responses` (harness) for ERROR/incomplete answers."""

    def __init__(self):
        super(ReleaseController, self).__init__()
        self.release_member = False
        self.after_delete = False
        self.released_nv = copy.deepcopy(RELEASED)
        self.released_policy = TRUNK
        self.fail_after_delete = set()
        self.extra_after_delete = []
        self.keep_parent = False
        self.modify_mode = "store"
        self.lossy_change = ("DEBOUNCE_TIMER", None)

    def __call__(self, mod, method, path, data=None):
        if self.after_delete and method == "GET" and any(m in path for m in self.fail_after_delete):
            self.calls.append((method, path, data))
            return dict(ERROR)
        if method == "DELETE" and path.endswith(MARKDELETE):
            self.calls.append((method, path, data))
            self.after_delete = True
            if not self.keep_parent:
                self.detail.pop(PO, None)
                self.po_names.discard(PO)
            self.detail[MEM] = {"policy": self.released_policy, "nvPairs": copy.deepcopy(self.released_nv)}
            self.policies_extra = list(self.extra_after_delete)
            return markdelete_ok(data)
        resp = super(ReleaseController, self).__call__(mod, method, path, data)
        if method == "POST" and path.endswith(MODIFY) and MEM in self.detail:
            nv = self.detail[MEM]["nvPairs"]
            if self.modify_mode == "lossy":
                key, value = self.lossy_change
                if value is None:
                    nv.pop(key, None)
                else:
                    nv[key] = value
            elif self.modify_mode == "keep_up":
                nv["ADMIN_STATE"] = "true"
        return resp

    def writes(self):
        return [c for c in self.calls if c[0] in ("POST", "PUT", "DELETE") and "/config-preview" not in c[1]]

    def write_kinds(self):
        out = []
        for c in self.writes():
            out.append("markdelete" if c[1].endswith(MARKDELETE) else "modify" if c[1].endswith(MODIFY) else "deploy" if c[1].endswith(DEPLOY) else c[1])
        return out

    def modify_bodies(self):
        return [json.loads(c[2]) for c in self.calls if c[0] == "POST" and c[1].endswith(MODIFY)]

    def phase_order(self):
        """The ordered phases of the deletion invocation: writes, the fresh reads between them and the preview."""
        out = []
        for m, p, _d in self.calls:
            if m == "DELETE" and p.endswith(MARKDELETE):
                out.append("markdelete")
            elif m == "POST" and p.endswith(MODIFY):
                out.append("modify")
            elif m == "POST" and p.endswith(DEPLOY):
                out.append("deploy")
            elif "/config-preview/" in p:
                out.append("preview")
            elif m == "GET" and (SUMMARY in p or POLICIES in p or DETAIL in p):
                out.append("read")
        compact = []
        for x in out:
            if not (compact and compact[-1] == x == "read"):
                compact.append(x)
        return compact


def owned_ctrl(**knobs):
    """The MEASURED H1-post parent and member, ready for `deleted` (parent/member intents + the policy shape)."""
    ctrl = ReleaseController()
    ctrl.detail[PO] = {"policy": P.PO_HOST_POLICY, "nvPairs": harness_nv(stage("H1-post")["intent"][PO_NAME]["nvPairs"])}
    ctrl.po_names.add(PO)
    ctrl.detail[MEM] = {"policy": PO_MEMBER, "nvPairs": harness_nv(stage("H1-post")["intent"][MEM]["nvPairs"])}
    for k, v in knobs.items():
        setattr(ctrl, k, v)
    if "previews" not in knobs:
        ctrl.previews = [entry("H1-verify")]
    return ctrl


def delete(ctrl):
    return run(ctrl, [{"name": "po502", "switch": [SWITCH_IP], "deploy": True}], state="deleted")


Q56 = load_case("pvlan_release_routed_q56_measured")


CDP_RELEASE = load_case("pvlan_release_routed_cdp_measured")


ROUTED = "int_routed_host"


RELEASED_ROUTED = dict(Q56["released_routed_nvpairs"])  # MEASURED, ADMIN_STATE "true"


RELEASED_ROUTED_CDP = dict(CDP_RELEASE["released_routed_nvpairs"])  # MEASURED on NDFC 12.6.0.267: the Q56 keys plus CDP_ENABLE and two inactive keys


CHILDREN_UP = [(c["templateName"], c["priority"]) for c in Q56["released_children"]]  # MEASURED own children


def remap(lines, port, po_number, pair):
    """The measured lines on the harness names (port, Po number, association)."""
    out = []
    for line in lines:
        line = line.replace("ethernet1/8", port.lower()).replace("Ethernet1/8", port)
        line = line.replace("port-channel521", "port-channel%s" % po_number).replace("channel-group 521", "channel-group %s" % po_number)
        out.append(line.replace("2410 2412", "%d %d" % pair))
    return out


def routed_release_preview(port=MEM, po_number="502", pair=(2210, 2212), admin_up=False, form="measured"):
    """MEASURED release preview (admin_up=True), the MEASURED preview after the module-equivalent modify (admin_up=False, the default
    form), or the DERIVED admin-down form of the RA1 battery (form="derived": `no shutdown` dropped from the measured release preview)."""
    pv = Q56["preview_release_admin_up"] if admin_up or form == "derived" else Q56["preview_release_admin_down_measured"]
    pending = remap(pv["pendingConfig"], port, po_number, pair)
    expected = remap(pv["expected_member"], port, po_number, pair)
    if not admin_up and form == "derived":
        pending = [line for line in pending if line.strip() != "no shutdown"]
        expected = [("  shutdown" if line.strip() == "no shutdown" else line) for line in expected]
    return pending, remap(pv["running_member"], port, po_number, pair), expected


def child_policies(port, templates, serial="x"):
    return [{"entityName": port, "entityType": "INTERFACE", "templateName": t, "source": port, "deleted": False,
             "policyId": "POLICY-77%03d" % i, "priority": prio, "serialNumber": serial} for i, (t, prio) in enumerate(templates)]


# ------------------------------------------------------------------ Po: refused before any member write
def own(port, template, source=None, prio=452):
    return {"entityName": port, "entityType": "INTERFACE", "templateName": template, "source": port if source is None else source,
            "deleted": False, "policyId": "POLICY-779%02d" % (len(template) % 97), "priority": prio, "serialNumber": "x"}
