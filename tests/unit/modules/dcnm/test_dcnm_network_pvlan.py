# Copyright (c) 2026 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
from unittest.mock import patch

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import dcnm_get_bulk_api_support
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_network
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

FABRIC = "test_network"
REST = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest"
NETS = REST + "/top-down/fabrics/" + FABRIC + "/networks"
ATTACH = NETS + "/attachments"
# DcnmNetwork rewrites this class-level table in place for multicluster fabrics,
# and other tests in the same process run those paths. Keep a clean copy.
PATHS = copy.deepcopy(dcnm_network.DcnmNetwork.dcnm_network_paths)
SN = {"leaf11": "PVL0000011", "leaf12": "PVL0000012", "leaf13": "PVL0000013", "leaf14": "PVL0000014"}
IP = {"leaf11": "192.0.2.11", "leaf12": "192.0.2.12", "leaf13": "192.0.2.13", "leaf14": "192.0.2.14"}


def ok(method, path, data):
    return {"RETURN_CODE": 200, "METHOD": method, "MESSAGE": "OK", "REQUEST_PATH": path, "DATA": data}


def bad(method, path, message):
    return {"RETURN_CODE": 400, "METHOD": method, "MESSAGE": "Bad Request", "REQUEST_PATH": path, "DATA": {"message": message}}


class FakeNdfc(object):
    """
    Network API of one standalone fabric, limited to behavior observed on
    NDFC 12.6 with PVLAN networks:

    - a secondary needs a valid primaryNetworkId; a name-only link is refused;
    - one isolated secondary per primary;
    - a primary with a secondary cannot be deleted;
    - attaching a secondary adds its primary on that switch, and attaching a
      primary adds the secondaries already attached elsewhere; these rows have
      no marker;
    - a primary detach under an explicit secondary on the same switch is
      refused per item inside HTTP 200;
    - after a secondary detach an implicit primary row reads isLanAttached
      false / PENDING;
    - a detach of an implicit primary row is refused per item inside HTTP 200,
      also after the row was withdrawn with its last secondary;
    - a PUT replaces the stored template config;
    - an attach or port-change item (deployment true) of a vPC switch whose
      peer is not named for the same network in the same POST is refused per
      item inside HTTP 200 ("VPC details not found for Peer Serial no"), as
      measured for a port detach of one peer. A detach item (deployment false)
      of one peer alone is applied: its answer is not measured.

    Deploy handling: a deploy makes the named attached rows DEPLOYED and
    removes the named rows that are detached (PENDING or OUT-OF-SYNC), as
    measured for a network deploy that named every family member. A network
    deploy changes only the rows it names; whether NDFC also deploys an
    unnamed implicit primary is not measured.
    """

    def __init__(self, fixtures, inventory):
        self.fixtures = fixtures
        self.inventory = inventory
        self.networks = {}
        self.rows = {}
        self.vrfs = ["VRF_A"]
        self.policies = {}
        self.requests = []
        self.inject = []
        # (method, network name) -> error response, returned once instead of the create or delete.
        self.fail_network = {}
        # (network name, serial) -> item text. The item is refused and not applied; the other items of
        # the same POST are applied (assumption: items are independent, as the per-item response suggests).
        # The refusal stays until removed from this table.
        self.refuse = {}
        # (network name, serial) rows that a deploy leaves unchanged.
        self.stuck = set()
        # network name -> networkStatus returned by the network list instead of the one derived from the rows.
        self.status_override = {}
        self.next_l2vni = 30900
        # (network name, serial) of every applied detach item whose vPC peer was not in the same POST (not measured).
        self.lone_vpc_detaches = []

    # ----- seeding -----------------------------------------------------------

    def seed(self, kind, name, net_id, vlan, primary=None, vrf=None, gui_shape=False, **template):
        """Add a network in the captured GET shape. Unless gui_shape is set, the two boolean
        fields the captured GUI-created objects leave empty read "false", as after a module write."""
        obj = copy.deepcopy(self.fixtures["controller_network_" + ("primary_l2" if kind == "regular" else kind)])
        conf = json.loads(obj["networkTemplateConfig"])
        conf.update({"networkName": name, "vlanId": str(vlan), "segmentId": str(net_id)})
        if kind == "regular":
            conf["type"] = "Normal"
        if not gui_shape:
            for key in ("suppressArp", "trmEnabled"):
                if conf.get(key) == "":
                    conf[key] = "false"
        conf.update(template)
        obj.update({"networkName": name, "displayName": name, "networkId": net_id, "fabric": FABRIC})
        obj["networkTemplateConfig"] = json.dumps(conf)
        if primary is not None:
            obj["primaryNetworkId"] = self.networks[primary]["networkId"]
        if vrf is not None:
            obj["vrf"] = vrf
        if kind == "regular":
            obj["type"] = "Normal"
        self.networks[name] = obj
        return obj

    def attach(self, name, switch, explicit=True, state="DEPLOYED", ports="", instance=None):
        serial = SN[switch]
        self.rows[(name, serial)] = {"attached": True, "state": state, "ports": ports, "explicit": explicit, "instance": instance}
        net = self.networks[name]
        if net["type"] in ("Isolated", "Community"):
            primary = self.by_id(net["primaryNetworkId"])
            if not self.rows.get((primary["networkName"], serial), {}).get("attached"):
                self.rows[(primary["networkName"], serial)] = {"attached": True, "state": state, "ports": "", "explicit": False}

    # ----- helpers -----------------------------------------------------------

    def by_id(self, network_id):
        for net in self.networks.values():
            if net["networkId"] == network_id:
                return net
        return None

    def secondaries(self, primary_name):
        primary_id = self.networks[primary_name]["networkId"]
        return [net["networkName"] for net in self.networks.values() if net["type"] in ("Isolated", "Community") and net["primaryNetworkId"] == primary_id]

    def switch_name(self, serial):
        for data in self.inventory.values():
            if data["serialNumber"] == serial:
                return data["logicalName"]
        return serial

    @staticmethod
    def stringify(conf):
        conf = json.loads(conf) if isinstance(conf, str) else dict(conf)
        for key, value in list(conf.items()):
            if isinstance(value, bool):
                conf[key] = "true" if value else "false"
            elif isinstance(value, int):
                conf[key] = str(value)
            elif value is None:
                conf[key] = ""
        return json.dumps(conf)

    def status(self, name):
        states = [row["state"] for (net, serial), row in self.rows.items() if net == name]
        for state in ("PENDING", "OUT-OF-SYNC", "DEPLOYED"):
            if state in states:
                return state
        return "NA"

    def writes(self):
        return [request for request in self.requests if request[0] != "GET"]

    def attached(self, name):
        return sorted(serial for (net, serial), row in self.rows.items() if net == name and row["attached"])

    # ----- API ---------------------------------------------------------------

    def get_url(self, module, fabric, path, items, module_name):
        return self.send(module, "GET", path.format(fabric, items))

    def send(self, module, method, path, data=None):
        body = json.loads(data) if isinstance(data, str) and data else data
        self.requests.append((method, path, copy.deepcopy(body)))
        # inject entries: (method, path suffix, response[, matching calls to let through first])
        for index, entry in enumerate(self.inject):
            if entry[0] == method and path.endswith(entry[1]):
                if len(entry) > 3 and entry[3] > 0:
                    self.inject[index] = entry[:3] + (entry[3] - 1,)
                    break
                self.inject.pop(index)
                return entry[2]

        if method == "GET":
            return self.get(path)
        if method == "POST" and path == NETS:
            return self.create(method, path, body)
        if method == "POST" and path == REST + "/top-down/bulk-create/networks":
            results = [self.create(method, path, item) for item in body]
            return results[-1] if results else ok(method, path, {})
        if method == "PUT" and path.startswith(NETS + "/"):
            return self.update(method, path, path[len(NETS) + 1:], body)
        if method == "PUT" and path == REST + "/top-down/v2/bulk-update/networks":
            for item in body:
                item = dict(item, networkTemplateConfig=json.dumps(item["networkTemplateConfig"]))
                self.update(method, path, item["networkName"], item)
            return ok(method, path, {})
        if method == "DELETE" and path.startswith(NETS + "/"):
            return self.delete(method, path, path[len(NETS) + 1:])
        if method == "DELETE" and "/bulk-delete/networks?network-names=" in path:
            for name in path.split("=", 1)[1].split(","):
                response = self.delete(method, path, name)
                if response["RETURN_CODE"] != 200:
                    return response
            return ok(method, path, {})
        if method == "POST" and path == ATTACH:
            return self.attachments(method, path, body)
        if method == "POST" and "/config-deploy/" in path:
            serials = path.split("/config-deploy/", 1)[1].split("?", 1)[0].split(",")
            self.deploy({(name, serial) for (name, serial) in self.rows if serial in serials})
            return ok(method, path, {"status": "Configuration deployment completed."})
        if method == "POST" and path == REST + "/top-down/networks/deploy":
            keys = set()
            for serial, names in body.items():
                keys |= {(name, serial) for name in names.split(",")}
            self.deploy(keys)
            return ok(method, path, {"status": "Deployment of network(s) has been initiated successfully"})
        raise AssertionError("unexpected request {0} {1}".format(method, path))

    def get(self, path):
        if path == REST + "/top-down/fabrics/" + FABRIC + "/vrfs":
            return ok("GET", path, [{"vrfName": vrf} for vrf in self.vrfs])
        if path == NETS:
            return ok("GET", path, [dict(net, networkStatus=self.status_override.get(name) or self.status(name)) for name, net in self.networks.items()])
        if path.startswith(NETS + "?vrf-name="):
            vrf = path.split("=", 1)[1]
            return ok("GET", path, [copy.deepcopy(net) for net in self.networks.values() if net["vrf"] == vrf])
        if path.startswith(ATTACH + "?network-names="):
            # One entry per network even when a name repeats in the query (assumption).
            names = list(dict.fromkeys(path.split("=", 1)[1].split(",")))
            return ok("GET", path, [self.attach_entry(name) for name in names if name in self.networks])
        if path == REST + "/top-down/fabrics/" + FABRIC + "/netinfo":
            self.next_l2vni += 1
            return ok("GET", path, {"l2vni": self.next_l2vni})
        if path.startswith(REST + "/resource-manager/vlan/"):
            return ok("GET", path, 3001)
        if path.startswith(REST + "/control/policies/switches?serialNumber="):
            return ok("GET", path, copy.deepcopy(self.policies.get(path.split("=", 1)[1], [])))
        if path.startswith(NETS + "/"):
            name = path[len(NETS) + 1:]
            if name not in self.networks:
                return bad("GET", path, "Invalid network name")
            return ok("GET", path, copy.deepcopy(self.networks[name]))
        raise AssertionError("unexpected GET " + path)

    def attach_entry(self, name):
        net = self.networks[name]
        rows = []
        for data in self.inventory.values():
            if data["switchRole"] == "spine":
                continue
            serial = data["serialNumber"]
            row = self.rows.get((name, serial))
            rows.append({
                "networkName": name,
                "displayName": name,
                "switchName": data["logicalName"],
                "switchRole": data["switchRole"],
                "fabricName": FABRIC,
                "lanAttachState": row["state"] if row else "NA",
                "isLanAttached": bool(row and row["attached"]),
                "portNames": row["ports"] if row else "",
                "switchSerialNo": serial,
                "peerSerialNo": data.get("peerSerialNumber"),
                "switchDbId": 1000,
                "ipAddress": data["ipAddress"],
                "networkId": net["networkId"],
                "vlanId": int(json.loads(net["networkTemplateConfig"]).get("vlanId") or 0),
                "instanceValues": (row.get("instance") or '{"sviEnabled":"true"}') if row else None,
                "entityName": name,
                "interfaceGroups": None,
            })
        return {"networkName": name, "lanAttachList": rows}

    def create(self, method, path, body):
        name = body["networkName"]
        if ("POST", name) in self.fail_network:
            return self.fail_network.pop(("POST", name))
        net_type = body.get("type") or "Normal"
        primary_id = body.get("primaryNetworkId", -1)
        if net_type in ("Isolated", "Community"):
            primary = self.by_id(primary_id)
            if primary is None or primary["type"] != "Primary":
                return bad(method, path, "Invalid primary network for " + name)
            if net_type == "Isolated" and any(
                net["type"] == "Isolated" and net["primaryNetworkId"] == primary_id for net in self.networks.values()
            ):
                return bad(method, path, "Only one secondary isolated network is allowed to be associated with a primary network.")
        self.networks[name] = {
            "fabric": FABRIC,
            "networkName": name,
            "displayName": body.get("displayName", name),
            "networkId": body["networkId"],
            "networkTemplate": body["networkTemplate"],
            "networkExtensionTemplate": body["networkExtensionTemplate"],
            "networkTemplateConfig": self.stringify(body["networkTemplateConfig"]),
            "vrf": body.get("vrf"),
            "tenantName": "",
            "serviceNetworkTemplate": None,
            "source": None,
            "interfaceGroups": None,
            "primaryNetworkId": primary_id,
            "type": net_type,
            "primaryNetworkName": None,
            "vlanId": None,
            "vlanName": None,
            "hierarchicalKey": FABRIC,
        }
        return ok(method, path, {"Network Id": body["networkId"], "Network Name": name})

    def update(self, method, path, name, body):
        net = self.networks.get(name)
        if net is None:
            return bad(method, path, "Invalid network name")
        primary_id = body.get("primaryNetworkId", net["primaryNetworkId"])
        if primary_id != net["primaryNetworkId"] and any(row["attached"] for (other, serial), row in self.rows.items() if other == name):
            return bad(method, path, "Type change is not allowed as the network has existing attachments")
        net.update({
            "networkTemplateConfig": self.stringify(body["networkTemplateConfig"]),
            "networkTemplate": body["networkTemplate"],
            "networkExtensionTemplate": body["networkExtensionTemplate"],
            "vrf": body["vrf"],
            "primaryNetworkId": primary_id,
            "type": body.get("type", net["type"]),
            "interfaceGroups": "",
        })
        return ok(method, path, {})

    def delete(self, method, path, name):
        net = self.networks.get(name)
        if net is None:
            return bad(method, path, "Invalid network name")
        if ("DELETE", name) in self.fail_network:
            return self.fail_network.pop(("DELETE", name))
        if net["type"] == "Primary" and self.secondaries(name):
            return bad(method, path, "Primary network cannot be deleted if a secondary network is associated with it.")
        del self.networks[name]
        for key in [key for key in self.rows if key[0] == name]:
            del self.rows[key]
        return ok(method, path, {})

    def peer_of(self, serial):
        for data in self.inventory.values():
            if data["serialNumber"] == serial and data.get("isVpcConfigured"):
                return data.get("peerSerialNumber")
        return None

    def attachments(self, method, path, body):
        data = {}
        for entry in body:
            name = entry["networkName"]
            named = set(item["serialNumber"] for item in entry["lanAttachList"])
            for item in entry["lanAttachList"]:
                serial = item["serialNumber"]
                key = "{0}-[{1}/{2}]".format(name, serial, self.switch_name(serial))
                peer = self.peer_of(serial)
                if name not in self.networks:
                    data[key] = "Invalid network " + name
                elif (name, serial) in self.refuse:
                    data[key] = self.refuse[(name, serial)]
                elif item.get("deployment") and peer and peer not in named:
                    data[key] = self.fixtures["vpc_pair_measured"]["lone_port_detach_answer"].format(peer=peer)
                elif item.get("deployment"):
                    data[key] = self.attach_item(name, serial, item)
                else:
                    if peer and peer not in named:
                        self.lone_vpc_detaches.append((name, serial))
                    data[key] = self.detach_item(name, serial)
        return ok(method, path, data)

    def attach_item(self, name, serial, item):
        row = self.rows.get((name, serial)) or {"attached": False, "state": "NA", "ports": "", "explicit": False}
        ports = set(port for port in row["ports"].split(",") if port)
        ports |= set(port for port in (item.get("switchPorts") or "").split(",") if port)
        ports -= set(port for port in (item.get("detachSwitchPorts") or "").split(",") if port)
        row.update({"attached": True, "state": "OUT-OF-SYNC", "ports": ",".join(sorted(ports)), "explicit": True})
        self.rows[(name, serial)] = row
        net = self.networks[name]
        if net["type"] in ("Isolated", "Community"):
            primary = self.by_id(net["primaryNetworkId"])["networkName"]
            if not self.rows.get((primary, serial), {}).get("attached"):
                self.rows[(primary, serial)] = {"attached": True, "state": "OUT-OF-SYNC", "ports": "", "explicit": False}
        elif net["type"] == "Primary":
            for secondary in self.secondaries(name):
                elsewhere = any(row["attached"] for (other, other_serial), row in self.rows.items() if other == secondary and other_serial != serial)
                if elsewhere and not self.rows.get((secondary, serial), {}).get("attached"):
                    self.rows[(secondary, serial)] = {"attached": True, "state": "OUT-OF-SYNC", "ports": "", "explicit": False}
        return "SUCCESS"

    def detach_item(self, name, serial):
        net = self.networks[name]
        row = self.rows.get((name, serial))
        if net["type"] == "Primary":
            explicit = [s for s in self.secondaries(name) if self.rows.get((s, serial), {}).get("explicit") and self.rows[(s, serial)]["attached"]]
            if explicit:
                return (
                    "The following Secondary networks[{0}] have explicit attachment on switch[{1}] hence detach on "
                    "primary is not allowed".format(",".join(explicit), serial)
                )
            if row and not row["explicit"]:
                return (
                    "Network Attachment[{0}] is implicit attached on switch[{1}] and implicit attachments are not "
                    "allowed to be detached".format(name, serial)
                )
            for secondary in self.secondaries(name):
                if self.rows.get((secondary, serial), {}).get("attached"):
                    self.rows[(secondary, serial)].update({"attached": False, "state": "PENDING", "explicit": False})
        if row:
            row.update({"attached": False, "state": "PENDING", "explicit": False, "ports": ""})
        if net["type"] in ("Isolated", "Community"):
            primary = self.by_id(net["primaryNetworkId"])["networkName"]
            prow = self.rows.get((primary, serial))
            others = [s for s in self.secondaries(primary) if s != name and self.rows.get((s, serial), {}).get("attached")]
            if prow and prow["attached"] and not prow["explicit"] and not others:
                prow.update({"attached": False, "state": "PENDING"})
        return "SUCCESS"

    def deploy(self, keys):
        for key in keys:
            row = self.rows.get(key)
            if row is None or key in self.stuck:
                continue
            if row["attached"]:
                row["state"] = "DEPLOYED"
            else:
                del self.rows[key]


class TestDcnmNetworkPvlan(TestDcnmModule):

    module = dcnm_network
    fixtures = loadPlaybookData("dcnm_network_pvlan")

    def setUp(self):
        super(TestDcnmNetworkPvlan, self).setUp()
        self.ndfc = FakeNdfc(self.fixtures, copy.deepcopy(self.fixtures["inventory_pvlan"]))
        self.fabric_details = copy.deepcopy(self.fixtures["fabric_details_pvlan"])
        self.bulk_api = True
        self.patches = [
            patch("ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_send", side_effect=self.ndfc.send),
            patch("ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_get_url", side_effect=self.ndfc.get_url),
            patch(
                "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.get_nd_fabric_inventory_details",
                side_effect=lambda *args, **kwargs: copy.deepcopy(self.ndfc.inventory),
            ),
            patch(
                "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.get_nd_fabric_details",
                side_effect=lambda *args, **kwargs: copy.deepcopy(self.fabric_details),
            ),
            patch(
                "ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_get_bulk_api_support",
                side_effect=lambda *args, **kwargs: self.bulk_api,
            ),
            patch("ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.time.sleep"),
        ]
        for item in self.patches:
            item.start()
        self.saved_paths = dcnm_network.DcnmNetwork.dcnm_network_paths
        dcnm_network.DcnmNetwork.dcnm_network_paths = copy.deepcopy(PATHS)

    def tearDown(self):
        dcnm_network.DcnmNetwork.dcnm_network_paths = self.saved_paths
        for item in self.patches:
            item.stop()
        super(TestDcnmNetworkPvlan, self).tearDown()

    # ----- runners -----------------------------------------------------------

    def run_module(self, state, config=None, failed=False, check_mode=False, deploy_mode=None):
        args = {
            "fabric": FABRIC,
            "state": state,
            "_fabric_details": {"fabric_type": "standalone", "nd_version": 12.4, "ndfc_version": "12.6.0.267"},
        }
        if config is not None:
            args["config"] = copy.deepcopy(config)
        if deploy_mode:
            args["deploy_mode"] = deploy_mode
        if check_mode:
            args["_ansible_check_mode"] = True
        set_module_args(args)
        self.ndfc.requests = []
        return self.failed() if failed else self.result()

    def result(self):
        with self.assertRaises(dcnm_network_exit()) as exc:
            self.module.main()
        return exc.exception.args[0]

    def assert_no_writes(self):
        self.assertEqual(self.ndfc.writes(), [])

    @staticmethod
    def family(primary_attach=None, isolated_attach=None, community_attach=None, deploy=True, primary_type="primary"):
        config = [
            {"net_name": "pv-isolated", "net_id": 30011, "vlan_id": 2432, "pvlan_type": "isolated", "pvlan_primary": "pv-primary", "deploy": deploy},
            {"net_name": "pv-community", "net_id": 30012, "vlan_id": 2433, "pvlan_type": "community", "pvlan_primary": "pv-primary", "deploy": deploy},
            {"net_name": "pv-primary", "net_id": 30010, "vlan_id": 2431, "is_l2only": True, "pvlan_type": primary_type, "deploy": deploy},
        ]
        for entry, attach in zip(config, (isolated_attach, community_attach, primary_attach)):
            if attach is not None:
                entry["attach"] = [{"ip_address": IP[switch]} for switch in attach]
        return config

    def seed_family(self, isolated_on=(), community_on=(), primary_on=()):
        self.ndfc.seed("primary_l2", "pv-primary", 30010, 2431)
        self.ndfc.seed("isolated", "pv-isolated", 30011, 2432, primary="pv-primary")
        self.ndfc.seed("community", "pv-community", 30012, 2433, primary="pv-primary")
        for switch in primary_on:
            self.ndfc.attach("pv-primary", switch)
        for switch in isolated_on:
            self.ndfc.attach("pv-isolated", switch)
        for switch in community_on:
            self.ndfc.attach("pv-community", switch)

    def bodies(self, method, path):
        return [body for request_method, request_path, body in self.ndfc.requests if request_method == method and request_path == path]

    def attach_items(self):
        """Return (network, serial, deployment) for every attachment item sent, in order."""
        items = []
        for method, path, body in self.ndfc.requests:
            if method == "POST" and path == ATTACH:
                for entry in body:
                    for item in entry["lanAttachList"]:
                        items.append((entry["networkName"], item["serialNumber"], item["deployment"]))
        return items

    # ----- regular controls --------------------------------------------------

    def test_regular_requests_unchanged(self):
        """A request without PVLAN keys issues no PVLAN read and keeps the regular bodies."""
        self.ndfc.seed("regular", "reg-existing", 30100, 2100, vrf="VRF_A")
        config = [
            {"net_name": "reg-l2", "net_id": 30101, "vlan_id": 2101, "is_l2only": True,
             "attach": [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/10"]}]},
            {"net_name": "reg-routed", "net_id": 30102, "vlan_id": 2102, "vrf_name": "VRF_A", "gw_ip_subnet": "192.0.2.129/25",
             "attach": [{"ip_address": IP["leaf12"]}]},
        ]
        result = self.run_module("merged", config)
        self.assertTrue(result["changed"])
        self.assertEqual(self.bodies("GET", NETS), [], "no fabric network-list read for a regular request")
        bulk = self.bodies("POST", REST + "/top-down/bulk-create/networks")
        self.assertEqual(len(bulk), 1)
        self.assertEqual([net["networkName"] for net in bulk[0]], ["reg-l2", "reg-routed"])
        for net in bulk[0]:
            self.assertNotIn("type", net)
            self.assertNotIn("primaryNetworkId", net)
            self.assertNotIn("type", json.loads(net["networkTemplateConfig"]))
        attach = self.bodies("POST", ATTACH)
        self.assertEqual(len(attach), 1, "one attachments POST")
        ports = {item["serialNumber"]: item["switchPorts"] for entry in attach[0] for item in entry["lanAttachList"]}
        self.assertEqual(ports[SN["leaf11"]], "Ethernet1/10")
        self.assertNotIn("pvlan_type", json.dumps(result["diff"]))

    # ----- input validation --------------------------------------------------

    def test_non_standalone_fabric_rejected(self):
        """PVLAN options fail on MSD and MFD fabrics before any write."""
        for fabric_type in ("multisite_parent", "multisite_child", "multicluster_parent"):
            with self.subTest(fabric_type=fabric_type):
                set_module_args({
                    "fabric": FABRIC, "state": "merged", "config": self.family(),
                    "_fabric_details": {"fabric_type": fabric_type, "nd_version": 12.4, "ndfc_version": "12.6.0.267"},
                })
                self.ndfc.requests = []
                result = self.failed()
                self.assertIn("supported only on standalone fabrics", result["msg"])
                self.assert_no_writes()

    def test_input_validation(self):
        """Invalid type values and misplaced pvlan_primary fail before any write."""
        cases = [
            ([{"net_name": "x", "net_id": 1, "vlan_id": 2, "pvlan_type": "promiscuous"}], "Invalid choice"),
            ([{"net_name": "x", "net_id": 1, "vlan_id": 2, "is_l2only": True, "pvlan_primary": "pv-primary"}], "pvlan_primary requires pvlan_type"),
            ([{"net_name": "x", "net_id": 1, "vlan_id": 2, "is_l2only": True, "pvlan_type": "primary", "pvlan_primary": "y"}],
             "valid only for isolated or community"),
            ([{"net_name": "x", "net_id": 1, "vlan_id": 2, "pvlan_type": "isolated"}], "pvlan_primary is required"),
            ([{"net_name": "x", "net_id": 1, "vlan_id": 2, "pvlan_type": "isolated", "is_l2only": False, "pvlan_primary": "p"}], "Layer 2 only"),
        ]
        for config, message in cases:
            with self.subTest(message=message):
                result = self.run_module("merged", config, failed=True)
                self.assertIn(message, str(result["msg"]))
                self.assert_no_writes()

    def test_new_pvlan_requires_explicit_ids(self):
        """No automatic ID or VLAN for a new PVLAN network, and no allocation read."""
        for missing in ("net_id", "vlan_id"):
            with self.subTest(missing=missing):
                config = self.family()
                del config[2][missing]
                result = self.run_module("merged", config, failed=True)
                self.assertIn("a new PVLAN network requires " + missing, result["msg"])
                self.assert_no_writes()
                self.assertFalse([path for method, path, body in self.ndfc.requests if path.endswith("/netinfo")])

    def test_secondary_field_restrictions(self):
        """Fields the secondary template does not declare fail; unset values pass."""
        self.ndfc.seed("primary_l2", "pv-primary", 30010, 2431)
        for key, value in (("gw_ip_subnet", "192.0.2.1/24"), ("routing_tag", 100), ("dhcp_loopback_id", 0),
                           ("arp_suppress", True), ("int_desc", "x"), ("net_template", "Default_Network_Universal")):
            with self.subTest(key=key):
                config = [{"net_name": "pv-isolated", "net_id": 30011, "vlan_id": 2432, "pvlan_type": "isolated",
                           "pvlan_primary": "pv-primary", key: value}]
                result = self.run_module("merged", config, failed=True)
                self.assertIn(key, result["msg"])
                self.assert_no_writes()
        config = [{"net_name": "pv-isolated", "net_id": 30011, "vlan_id": 2432, "pvlan_type": "isolated", "pvlan_primary": "pv-primary",
                   "gw_ip_subnet": "", "arp_suppress": False, "int_desc": None, "net_template": "Pvlan_Secondary_Network"}]
        self.assertTrue(self.run_module("merged", config)["changed"])

    def test_primary_resolution_failures(self):
        """pvlan_primary must name a primary network other than itself."""
        self.ndfc.seed("regular", "reg-a", 30100, 2100)
        self.ndfc.seed("primary_l2", "pv-primary", 30010, 2431)
        self.ndfc.seed("community", "pv-community", 30012, 2433, primary="pv-primary")
        for primary, message in (("missing", "was not found"), ("reg-a", "is not a primary"),
                                 ("pv-community", "is not a primary"), ("pv-isolated", "itself")):
            with self.subTest(primary=primary):
                config = [{"net_name": "pv-isolated", "net_id": 30011, "vlan_id": 2432, "pvlan_type": "isolated", "pvlan_primary": primary}]
                result = self.run_module("merged", config, failed=True)
                self.assertIn(message, result["msg"])
                self.assert_no_writes()

    def test_one_isolated_per_primary(self):
        """Counts the request and the controller."""
        result = self.run_module("merged", self.family() + [
            {"net_name": "pv-isolated-2", "net_id": 30013, "vlan_id": 2434, "pvlan_type": "isolated", "pvlan_primary": "pv-primary"}], failed=True)
        self.assertIn("can have one isolated network", result["msg"])
        self.assert_no_writes()
        self.seed_family()
        result = self.run_module("merged", [
            {"net_name": "pv-isolated-2", "net_id": 30013, "vlan_id": 2434, "pvlan_type": "isolated", "pvlan_primary": "pv-primary"}], failed=True)
        self.assertIn("pv-isolated, pv-isolated-2", result["msg"])
        self.assert_no_writes()

    def test_fabric_pvlan_prerequisite(self):
        """ENABLE_PVLAN must be true; string and boolean forms are accepted."""
        for value, passes in (("false", False), (None, False), ("true", True), (True, True), ("TRUE", True)):
            with self.subTest(value=value):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                if value is None:
                    self.fabric_details["nvPairs"].pop("ENABLE_PVLAN", None)
                else:
                    self.fabric_details["nvPairs"]["ENABLE_PVLAN"] = value
                if passes:
                    self.assertTrue(self.run_module("merged", self.family())["changed"])
                else:
                    result = self.run_module("merged", self.family(), failed=True)
                    self.assertIn("ENABLE_PVLAN", result["msg"])
                    self.assert_no_writes()

    def test_mixed_request_no_write_before_reject(self):
        """An automatic-ID regular entry is not POSTed before a later PVLAN or VRF error."""
        self.ndfc.seed("regular", "reg-existing", 30100, 2100, vrf="VRF_A")
        self.ndfc.vrfs.append("VRF_B")
        auto = {"net_name": "reg-auto", "vrf_name": "VRF_A", "gw_ip_subnet": "192.0.2.129/25"}
        later = [
            {"net_name": "pv-isolated", "net_id": 30011, "vlan_id": 2432, "pvlan_type": "isolated", "pvlan_primary": "missing"},
            {"net_name": "reg-existing", "vrf_name": "VRF_B"},
        ]
        for entry in later:
            with self.subTest(entry=entry["net_name"]):
                config = [auto, entry]
                if entry["net_name"] == "reg-existing":
                    config.append({"net_name": "pv-primary", "net_id": 30010, "vlan_id": 2431, "is_l2only": True, "pvlan_type": "primary"})
                self.run_module("merged", config, failed=True)
                self.assert_no_writes()
                self.assertNotIn("reg-auto", self.ndfc.networks)

    def test_named_ports_input(self):
        """PVLAN ports are Ethernet interfaces or port-channels; tor_ports and other names are refused before any write."""
        config = self.family()
        config[0]["attach"] = [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/41"]}]
        self.assertTrue(self.run_module("merged", config)["changed"])
        self.assertIn(("pv-isolated", SN["leaf11"], "Ethernet1/41", "", True), self.port_items())

        self.ndfc.networks, self.ndfc.rows = {}, {}
        for ports in (["vPC543"], ["loopback0"], ["Vlan2431"]):
            with self.subTest(ports=ports):
                config = self.family()
                config[0]["attach"] = [{"ip_address": IP["leaf13"], "ports": ports}, {"ip_address": IP["leaf14"], "ports": ports}]
                result = self.run_module("merged", config, failed=True)
                self.assertIn("is not an Ethernet or Port-channel interface", result["msg"])
                self.assert_no_writes()
        config = self.family()
        config[0]["attach"] = [{"ip_address": IP["leaf11"], "tor_ports": [{"ip_address": IP["leaf12"], "ports": ["Ethernet1/1"]}]}]
        result = self.run_module("merged", config, failed=True)
        self.assertIn("tor_ports are not supported for PVLAN networks", result["msg"])
        self.assert_no_writes()

    # ----- identity ----------------------------------------------------------

    def test_conversion_rejected(self):
        """The type of an existing network cannot change."""
        self.ndfc.seed("regular", "reg-a", 30100, 2100)
        self.seed_family()
        for config, message in (
            ([{"net_name": "reg-a", "pvlan_type": "primary", "is_l2only": True}], "from regular to primary"),
            ([{"net_name": "pv-primary", "pvlan_type": "isolated", "pvlan_primary": "reg-a"}], "from primary to isolated"),
            ([{"net_name": "pv-isolated", "pvlan_type": "community", "pvlan_primary": "pv-primary"}], "from isolated to community"),
        ):
            for state in ("merged", "replaced"):
                with self.subTest(message=message, state=state):
                    result = self.run_module(state, config, failed=True)
                    self.assertIn(message, result["msg"])
                    self.assert_no_writes()

    def test_reparent_rejected(self):
        """The primary of an existing secondary cannot change."""
        self.seed_family()
        self.ndfc.seed("primary_routed", "pv-primary-rt", 30020, 2440)
        result = self.run_module("merged", [{"net_name": "pv-community", "pvlan_type": "community", "pvlan_primary": "pv-primary-rt"}], failed=True)
        self.assertIn("cannot change pvlan_primary", result["msg"])
        self.assert_no_writes()

    def test_omitted_keys_preserve_identity(self):
        """Omitted PVLAN keys keep the type and primary; no write when nothing else changes."""
        self.seed_family(isolated_on=("leaf11",))
        conf = json.loads(self.ndfc.networks["pv-isolated"]["networkTemplateConfig"])
        mcast = conf["mcastGroup"]
        config = [
            {"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": mcast, "attach": [{"ip_address": IP["leaf11"]}]},
            {"net_name": "pv-primary", "net_id": 30010, "vlan_id": 2431, "is_l2only": True, "multicast_group_address": mcast,
             "attach": [{"ip_address": IP["leaf11"]}]},
        ]
        for state in ("merged", "replaced"):
            with self.subTest(state=state):
                result = self.run_module(state, config)
                self.assertFalse(result["changed"], result)
                self.assert_no_writes()

    # ----- builders and transport --------------------------------------------

    def test_family_create_order_and_bodies(self):
        """Primary first, one POST per network even with the bulk API available; repeated after a delete."""
        for attempt in ("create", "recreate"):
            with self.subTest(attempt=attempt):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                result = self.run_module("merged", self.family(isolated_attach=("leaf11",)))
                self.assertTrue(result["changed"])
                self.assertEqual(self.bodies("POST", REST + "/top-down/bulk-create/networks"), [])
                creates = self.bodies("POST", NETS)
                self.assertEqual([body["networkName"] for body in creates], ["pv-primary", "pv-isolated", "pv-community"])
                primary, isolated, community = creates
                self.assertEqual((primary["type"], primary["primaryNetworkId"]), ("Primary", -1))
                self.assertEqual(json.loads(primary["networkTemplateConfig"])["type"], "Primary")
                self.assertEqual(primary["networkTemplate"], "Default_Network_Universal")
                for body, net_type in ((isolated, "Isolated"), (community, "Community")):
                    self.assertEqual(body["type"], net_type)
                    self.assertEqual(body["primaryNetworkId"], 30010)
                    self.assertEqual(body["networkTemplate"], "Pvlan_Secondary_Network")
                    self.assertEqual(body["networkExtensionTemplate"], "Pvlan_Secondary_Network")
                    self.assertEqual(body["vrf"], "NA")
                    conf = json.loads(body["networkTemplateConfig"])
                    self.assertEqual(conf["type"], net_type)
                    self.assertEqual(conf["primaryNetworkName"], "")
                    self.assertEqual(conf["segmentId"], body["networkId"])
                    self.assertEqual(
                        set(conf),
                        {"networkName", "vlanId", "vlanName", "type", "primaryNetworkName", "segmentId", "rtBothAuto",
                         "mcastGroup", "isLayer2Only", "networkMode", "vrfName", "xconnect"},
                    )
                    self.assertNotIn("primaryNetworkName", {key for key, value in body.items() if value})
                self.assertEqual(self.attach_items(), [("pv-isolated", SN["leaf11"], True)])
                self.assertEqual(self.ndfc.attached("pv-primary"), [SN["leaf11"]], "implicit primary row")
                repeat = self.run_module("merged", self.family(isolated_attach=("leaf11",)))
                self.assertFalse(repeat["changed"], repeat)

    def test_routed_primary_create(self):
        """A routed primary keeps its VRF and gateway and adds the type."""
        config = [{"net_name": "pv-primary-rt", "net_id": 30020, "vlan_id": 2440, "vrf_name": "VRF_A",
                   "gw_ip_subnet": "192.0.2.1/24", "pvlan_type": "primary"}]
        self.assertTrue(self.run_module("merged", config)["changed"])
        body = self.bodies("POST", NETS)[0]
        conf = json.loads(body["networkTemplateConfig"])
        self.assertEqual((body["vrf"], conf["gatewayIpAddress"], conf["type"]), ("VRF_A", "192.0.2.1/24", "Primary"))
        self.assertFalse(self.run_module("merged", config)["changed"])

    def test_update_full_template_config(self):
        """PVLAN updates go through the per-network PUT with the full stored template config."""
        self.seed_family()
        self.ndfc.seed("regular", "reg-a", 30100, 2100)
        stored_secondary = json.loads(self.ndfc.networks["pv-isolated"]["networkTemplateConfig"])
        stored_primary = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])
        config = [
            {"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "vlan_name": "ISO_NEW"},
            {"net_name": "reg-a", "is_l2only": True, "vlan_name": "REG_NEW"},
        ]
        self.assertTrue(self.run_module("merged", config)["changed"])
        puts = [(path, body) for method, path, body in self.ndfc.requests if method == "PUT"]
        self.assertEqual([path for path, body in puts], [REST + "/top-down/v2/bulk-update/networks", NETS + "/pv-isolated"])
        body = puts[1][1]
        self.assertEqual((body["type"], body["primaryNetworkId"], body["networkTemplate"]), ("Isolated", 30010, "Pvlan_Secondary_Network"))
        sent = json.loads(body["networkTemplateConfig"])
        self.assertEqual(set(sent), set(stored_secondary), "no stored key is dropped")
        self.assertEqual(sent["vlanName"], "ISO_NEW")
        for key in ("segmentId", "nveId", "enableIR", "networkType", "primaryNetworkName", "networkMode"):
            self.assertEqual(sent[key], stored_secondary[key])
        for key in ("networkStatus", "tenantName", "interfaceGroups", "hierarchicalKey"):
            self.assertNotIn(key, body)
        self.assertFalse(self.run_module("merged", config)["changed"])

        self.ndfc.requests = []
        config = [{"net_name": "pv-primary", "net_id": 30010, "vlan_id": 2431, "is_l2only": True, "vlan_name": "PRI_NEW",
                   "multicast_group_address": stored_primary["mcastGroup"]}]
        self.assertTrue(self.run_module("replaced", config)["changed"])
        body = self.bodies("PUT", NETS + "/pv-primary")[0]
        sent = json.loads(body["networkTemplateConfig"])
        self.assertEqual((sent["type"], sent["vlanName"]), ("Primary", "PRI_NEW"))
        for key in ("igmpVersion", "networkType", "nveId", "segmentId", "createSvi"):
            self.assertEqual(sent[key], stored_primary[key], key)
        self.assertEqual(self.bodies("PUT", REST + "/top-down/v2/bulk-update/networks"), [])

    def test_primary_outside_request(self):
        """One network-list read resolves a primary that is not in the request."""
        self.ndfc.seed("primary_l2", "pv-primary", 30010, 2431)
        config = [{"net_name": "pv-isolated", "net_id": 30011, "vlan_id": 2432, "pvlan_type": "isolated", "pvlan_primary": "pv-primary"}]
        self.assertTrue(self.run_module("merged", config)["changed"])
        self.assertEqual(len(self.bodies("GET", NETS)), 1)
        self.assertEqual([body["networkName"] for body in self.bodies("POST", NETS)], ["pv-isolated"])
        self.assertEqual(self.bodies("POST", NETS)[0]["primaryNetworkId"], 30010)
        self.assertEqual(self.bodies("PUT", NETS + "/pv-primary"), [])

    def test_two_families_vpc_pair(self):
        """Each secondary resolves to its own primary; both vPC peers are attached."""
        config = self.family(isolated_attach=("leaf13", "leaf14")) + [
            {"net_name": "pv2-primary", "net_id": 30030, "vlan_id": 2450, "is_l2only": True, "pvlan_type": "primary"},
            {"net_name": "pv2-isolated", "net_id": 30031, "vlan_id": 2451, "pvlan_type": "isolated", "pvlan_primary": "pv2-primary",
             "attach": [{"ip_address": IP["leaf13"]}, {"ip_address": IP["leaf14"]}]},
        ]
        self.assertTrue(self.run_module("merged", config)["changed"])
        primary_ids = {body["networkName"]: body["primaryNetworkId"] for body in self.bodies("POST", NETS)}
        self.assertEqual(primary_ids["pv-isolated"], 30010)
        self.assertEqual(primary_ids["pv2-isolated"], 30030)
        self.assertEqual(self.ndfc.attached("pv2-primary"), [SN["leaf13"], SN["leaf14"]])
        self.assertFalse(self.run_module("merged", config)["changed"])
        result = self.run_module("merged", [dict(config[4], attach=[{"ip_address": IP["leaf13"]}])], failed=True)
        self.assertIn("configured for vPC", result["msg"])

    # ----- attachments and family closure ------------------------------------

    def test_implicit_primary_is_not_drift(self):
        """The controller-added primary row needs no write in merged or replaced."""
        self.seed_family(isolated_on=("leaf11",))
        conf = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])
        config = [
            {"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": conf["mcastGroup"],
             "attach": [{"ip_address": IP["leaf11"]}]},
            {"net_name": "pv-primary", "is_l2only": True, "vlan_id": 2431, "multicast_group_address": conf["mcastGroup"]},
        ]
        for state in ("merged", "replaced"):
            with self.subTest(state=state):
                result = self.run_module(state, config)
                self.assertFalse(result["changed"], result)

    def test_closure_keeps_primary_under_surviving_secondary(self):
        """Replaced does not detach a primary from a switch a surviving secondary needs."""
        self.seed_family(isolated_on=("leaf11",), community_on=("leaf12",), primary_on=("leaf11",))
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        config = [{"net_name": "pv-primary", "is_l2only": True, "vlan_id": 2431, "multicast_group_address": mcast, "attach": []}]
        result = self.run_module("replaced", config)
        self.assertFalse(result["changed"], result)
        self.assertEqual(self.ndfc.attached("pv-primary"), [SN["leaf11"], SN["leaf12"]])

    def history(self, primary_explicit):
        """Same readback from two histories: primary attached explicitly or added by the secondary attach."""
        self.seed_family()
        if primary_explicit:
            self.ndfc.attach("pv-primary", "leaf11")
        self.ndfc.attach("pv-isolated", "leaf11")
        return self.ndfc.attach_entry("pv-primary"), self.ndfc.attach_entry("pv-isolated")

    def test_history_equivalence_primary_not_wanted(self):
        """Secondary removed, primary not wanted: the detach is sent only for a row still attached."""
        readbacks = []
        for explicit in (True, False):
            with self.subTest(explicit=explicit):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                readbacks.append(self.history(explicit))
                mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
                config = [
                    {"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": mcast, "attach": [], "deploy": False},
                    {"net_name": "pv-primary", "is_l2only": True, "vlan_id": 2431, "multicast_group_address": mcast, "attach": [], "deploy": False},
                ]
                result = self.run_module("replaced", config)
                self.assertTrue(result["changed"])
                sent = self.attach_items()
                self.assertEqual(sent[0], ("pv-isolated", SN["leaf11"], False))
                if explicit:
                    self.assertEqual(sent[1:], [("pv-primary", SN["leaf11"], False)])
                else:
                    self.assertEqual(sent[1:], [])
                    self.assertTrue(any("removed with its secondary" in warning for warning in result["warnings"]))
                self.assertEqual(self.ndfc.attached("pv-primary"), [])
                self.assertEqual(self.ndfc.attached("pv-isolated"), [])
                self.assertFalse(self.run_module("replaced", config)["changed"])
        self.assertEqual(readbacks[0], readbacks[1])

    def test_history_equivalence_primary_wanted(self):
        """Secondary removed, primary wanted: the primary is attached first in both histories."""
        for explicit in (True, False):
            with self.subTest(explicit=explicit):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.history(explicit)
                mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
                config = [
                    {"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": mcast, "attach": [], "deploy": False},
                    {"net_name": "pv-primary", "is_l2only": True, "vlan_id": 2431, "multicast_group_address": mcast,
                     "attach": [{"ip_address": IP["leaf11"]}], "deploy": False},
                ]
                result = self.run_module("replaced", config)
                self.assertEqual(self.attach_items(), [("pv-primary", SN["leaf11"], True), ("pv-isolated", SN["leaf11"], False)])
                self.assertEqual(self.ndfc.attached("pv-primary"), [SN["leaf11"]])
                self.assertEqual(self.ndfc.attached("pv-isolated"), [])
                self.assertTrue(result["changed"])
                self.assertFalse(self.run_module("replaced", config)["changed"])

    def test_secondary_following_primary_is_kept(self):
        """A secondary row added when its primary was attached elsewhere is family state, not drift."""
        self.seed_family(isolated_on=("leaf11",))
        self.ndfc.attach_item("pv-primary", SN["leaf12"], {"switchPorts": ""})
        self.assertEqual(self.ndfc.attached("pv-isolated"), [SN["leaf11"], SN["leaf12"]])
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        config = [
            {"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": mcast, "attach": [{"ip_address": IP["leaf11"]}]},
            {"net_name": "pv-primary", "is_l2only": True, "vlan_id": 2431, "multicast_group_address": mcast,
             "attach": [{"ip_address": IP["leaf11"]}, {"ip_address": IP["leaf12"]}]},
        ]
        self.ndfc.deploy(set(self.ndfc.rows))
        result = self.run_module("replaced", config)
        self.assertFalse(result["changed"], result)

    def test_per_item_refusal_reported(self):
        """An item refused inside HTTP 200 fails the task without a rollback and reports the state."""
        self.seed_family(isolated_on=("leaf11",))
        self.ndfc.inject.append(("POST", ATTACH, ok("POST", ATTACH, {
            "pv-community-[PVL0000012/leaf-12]": (
                "Invalid Interfaces in leaf-12. The following interfaces are not in a valid host or secondary trunk mode: Ethernet1/9"
            ),
        })))
        before = len(self.ndfc.networks)
        result = self.run_module("merged", [{"net_name": "pv-community", "is_l2only": True, "attach": [{"ip_address": IP["leaf12"]}]}], failed=True)
        self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
        self.assertIn("Invalid Interfaces", json.dumps(result["msg"]["FAILED_ITEMS"]))
        self.assertIn("pv-community", result["pvlan_state"]["networks"])
        self.assertEqual(len(self.ndfc.networks), before)
        self.assertEqual([request for request in self.ndfc.writes() if request[0] == "DELETE"], [])

    def test_existing_named_ports_follow_the_state(self):
        """Existing named ports of a PVLAN network: merged keeps them, replaced without them detaches them and keeps the
        switch, deleted detaches the ports before the switch; query reports them."""
        self.seed_family()
        self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41")
        isolated = self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf11"]}])
        self.assertFalse(self.run_module("merged", [isolated])["changed"])
        self.ndfc.seed("regular", "reg-routed", 30100, 2100, vrf="VRF_A", isLayer2Only="false")
        query = self.run_module("query", [{"net_name": "pv-isolated"}])
        self.assertIn("Ethernet1/41", json.dumps(query["response"]))

        self.run_module("replaced", [isolated])
        self.assertEqual(self.port_items(), [("pv-isolated", SN["leaf11"], "", "Ethernet1/41", True)])
        self.assertEqual(self.ndfc.attached("pv-isolated"), [SN["leaf11"]])

        self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41")
        self.run_module("deleted", [{"net_name": "pv-isolated"}])
        self.assertEqual(self.port_posts()[:2], [[("pv-isolated", SN["leaf11"], "", "Ethernet1/41", True)],
                                                 [("pv-isolated", SN["leaf11"], "", "", False)]])
        self.assertNotIn("pv-isolated", self.ndfc.networks)

    def test_pvlan_config_policy_not_attachment_freeform(self):
        """The generated PVLAN_CONFIG policies are not read as attachment freeform."""
        self.seed_family(isolated_on=("leaf11",), primary_on=("leaf11",))
        conf = "vlan 2431\n  private-vlan association add 2432\n\ninterface Vlan2431\n  private-vlan mapping add 2432\n"
        self.ndfc.policies[SN["leaf11"]] = [
            {"policyId": "POLICY-100", "templateName": "switch_freeform", "source": "PVLAN_CONFIG", "entityName": "Switch",
             "secondaryEntityType": "Config_Profile", "secondaryEntityName": "pv-primary",
             "nvPairs": {"CONF": conf, "SECENTTYPE": "Config_Profile", "SECENTITY": "pv-primary"}},
            {"policyId": "POLICY-110", "templateName": "switch_freeform_config", "source": "POLICY-100", "entityName": "SWITCH",
             "secondaryEntityType": "Config_Profile", "secondaryEntityName": "pv-primary", "nvPairs": {"CONF": conf.strip()}},
        ]
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        config = [{"net_name": "pv-primary", "is_l2only": True, "vlan_id": 2431, "multicast_group_address": mcast,
                   "attach": [{"ip_address": IP["leaf11"]}]}]
        result = self.run_module("replaced", config)
        self.assertFalse(result["changed"], result)

    # ----- lifecycle ---------------------------------------------------------

    def test_delete_secondary_only(self):
        """Deleting a secondary leaves its primary."""
        self.seed_family(community_on=("leaf12",))
        result = self.run_module("deleted", [{"net_name": "pv-community"}])
        self.assertTrue(result["changed"])
        self.assertEqual([path for method, path, body in self.ndfc.writes() if method == "DELETE"], [NETS + "/pv-community"])
        self.assertIn("pv-primary", self.ndfc.networks)
        self.assertNotIn("pv-community", self.ndfc.networks)

    def test_delete_primary_with_surviving_secondary(self):
        """A primary cannot be deleted while a secondary that is not deleted references it."""
        self.seed_family()
        result = self.run_module("deleted", [{"net_name": "pv-primary"}, {"net_name": "pv-isolated"}], failed=True)
        self.assertIn("pv-community reference it", result["msg"])
        self.assert_no_writes()

    def test_delete_family_order(self):
        """Secondaries are deleted before the primary, one network at a time without a body (fake deploy model)."""
        self.seed_family(isolated_on=("leaf11",), community_on=("leaf12",))
        config = [{"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}]
        self.assertTrue(self.run_module("deleted", config)["changed"])
        deletes = [(path, body) for method, path, body in self.ndfc.writes() if method == "DELETE"]
        self.assertEqual([path for path, body in deletes], [NETS + "/pv-isolated", NETS + "/pv-community", NETS + "/pv-primary"])
        self.assertEqual([body for path, body in deletes], [None, None, None])
        detaches = [item for item in self.attach_items() if not item[2]]
        self.assertEqual(detaches[:2], [("pv-isolated", SN["leaf11"], False), ("pv-community", SN["leaf12"], False)])
        self.assertNotIn(("pv-primary", SN["leaf11"], False), detaches, "implicit primary rows go with their secondaries")
        self.assertEqual(self.ndfc.networks, {})
        self.assertFalse(self.run_module("deleted", config)["changed"])

    def test_overridden_removes_family(self):
        """Overridden and deleted without config remove the family in dependency order (fake deploy model)."""
        for state, config in (("overridden", [{"net_name": "reg-keep", "net_id": 30101, "vlan_id": 2101, "is_l2only": True}]),
                              ("overridden", []), ("deleted", None)):
            with self.subTest(state=state):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.ndfc.seed("regular", "reg-keep", 30101, 2101)
                self.seed_family(isolated_on=("leaf11",))
                self.assertTrue(self.run_module(state, config)["changed"])
                deletes = [path.rsplit("/", 1)[1] for method, path, body in self.ndfc.writes() if method == "DELETE" and path.startswith(NETS + "/")]
                self.assertEqual(deletes, ["pv-isolated", "pv-community", "pv-primary"])
                self.assertEqual("reg-keep" in self.ndfc.networks, bool(config))

    def test_overridden_keeps_family(self):
        """Overridden with the family listed removes only the regular network."""
        self.ndfc.seed("regular", "reg-gone", 30101, 2101)
        self.seed_family()
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        config = [dict(entry, multicast_group_address=mcast) for entry in self.family()]
        self.assertTrue(self.run_module("overridden", config)["changed"])
        self.assertEqual(sorted(self.ndfc.networks), ["pv-community", "pv-isolated", "pv-primary"])
        self.assertFalse([request for request in self.ndfc.writes() if "pv-" in request[1]])

    def test_overridden_primary_missing(self):
        """Overridden fails when a listed secondary would lose its primary."""
        self.seed_family()
        config = [{"net_name": "pv-isolated", "is_l2only": True}, {"net_name": "pv-community", "is_l2only": True}]
        result = self.run_module("overridden", config, failed=True)
        self.assertIn("cannot delete a primary network", result["msg"])
        self.assert_no_writes()

    def test_brownfield_gui_shape_adoption(self):
        """A family read in the GUI-created shape is adopted without a type change. The first
        merged run rewrites the empty trmEnabled of the primary as false (inherited merged
        normalization for every network); the PUT keeps every stored key except the per-server DHCP
        keys that merged replaces with dhcpServers, as for a regular network, and the second run is
        a no-op."""
        self.ndfc.seed("primary_l2", "pv-primary", 30010, 2431, gui_shape=True)
        self.ndfc.seed("isolated", "pv-isolated", 30011, 2432, primary="pv-primary", gui_shape=True)
        self.ndfc.attach("pv-isolated", "leaf11")
        stored = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])
        config = [
            {"net_name": "pv-primary", "is_l2only": True, "pvlan_type": "primary"},
            {"net_name": "pv-isolated", "is_l2only": True, "pvlan_type": "isolated", "pvlan_primary": "pv-primary",
             "attach": [{"ip_address": IP["leaf11"]}]},
        ]
        self.assertTrue(self.run_module("merged", config)["changed"])
        self.assertEqual([path for method, path, body in self.ndfc.writes()], [NETS + "/pv-primary"])
        sent = json.loads(self.bodies("PUT", NETS + "/pv-primary")[0]["networkTemplateConfig"])
        dhcp_keys = {"dhcpServerAddr1", "dhcpServerAddr2", "dhcpServerAddr3", "vrfDhcp", "vrfDhcp2", "vrfDhcp3"}
        self.assertEqual(set(sent), set(stored) - dhcp_keys)
        self.assertEqual((sent["suppressArp"], sent["trmEnabled"], sent["type"]), ("", False, "Primary"))
        self.assertFalse(self.run_module("merged", config)["changed"])

    def test_rerun_after_partial_create(self):
        """Primary created, secondary failed; the rerun creates only what is missing."""
        self.ndfc.inject.append(("POST", NETS, bad("POST", NETS, "simulated controller error")))
        self.ndfc.seed("primary_l2", "pv-primary", 30010, 2431)
        config = self.family()[:1] + self.family()[2:]
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        config[1]["multicast_group_address"] = mcast
        result = self.run_module("merged", config, failed=True)
        self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
        self.assertEqual(result["pvlan_state"]["networks"]["pv-isolated"], "absent")
        self.assertIn("pv-primary", self.ndfc.networks)
        self.assertTrue(self.run_module("merged", config)["changed"])
        self.assertEqual([body["networkName"] for body in self.bodies("POST", NETS)], ["pv-isolated"])
        self.assertFalse(self.run_module("merged", config)["changed"])

    def test_failure_mixed_partial_create(self):
        """Mixed request, secondary create refused: nothing is rolled back, the failure lists every requested
        network, the next identical run creates only the missing secondaries, and the run after is a no-op."""
        self.ndfc.fail_network[("POST", "pv-isolated")] = bad("POST", NETS, "simulated controller error")
        config = [{"net_name": "reg-l2", "net_id": 30101, "vlan_id": 2101, "is_l2only": True,
                   "attach": [{"ip_address": IP["leaf12"]}]}] + self.family(isolated_attach=("leaf11",))
        result = self.run_module("merged", config, failed=True)
        self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
        self.assertEqual(result["msg"]["DATA"], {"message": "simulated controller error"})
        self.assertEqual([response["RETURN_CODE"] for response in result["response"]], [200, 200, 400])
        self.assertEqual(
            [(write["method"], write["path"]) for write in result["acknowledged_writes"]],
            [("POST", REST + "/top-down/bulk-create/networks"), ("POST", NETS)],
        )
        self.assertIn("acknowledged writes remain applied", result["msg"]["ROLLBACK_RESULT"])
        state = result["pvlan_state"]["networks"]
        self.assertEqual((state["reg-l2"]["type"], state["pv-primary"]["type"]), ("Normal", "Primary"))
        self.assertEqual((state["pv-isolated"], state["pv-community"]), ("absent", "absent"), "absent from a valid read")
        self.assertNotIn("read_error", result["pvlan_state"])
        self.assertEqual(result["pvlan_state"]["attachments"], {})
        self.assertEqual(
            [(method, path.rsplit("/", 1)[1], body["networkName"] if method == "POST" and path == NETS else None)
             for method, path, body in self.ndfc.writes()],
            [("POST", "networks", None), ("POST", "networks", "pv-primary"), ("POST", "networks", "pv-isolated")],
        )
        self.assertEqual(sorted(self.ndfc.networks), ["pv-primary", "reg-l2"])
        self.assertEqual(self.ndfc.rows, {})

        result = self.run_module("merged", config)
        self.assertTrue(result["changed"])
        self.assertEqual([body["networkName"] for body in self.bodies("POST", NETS)], ["pv-isolated", "pv-community"])
        self.assertEqual(self.bodies("POST", REST + "/top-down/bulk-create/networks"), [])
        self.assertEqual([request for request in self.ndfc.writes() if request[0] == "PUT"], [])
        self.assertEqual(sorted(self.attach_items()), [("pv-isolated", SN["leaf11"], True), ("reg-l2", SN["leaf12"], True)])
        self.assertFalse(self.run_module("merged", config)["changed"])

    def test_failure_attach_refusal_mixed_rerun(self):
        """One item refused inside HTTP 200 in a mixed request: the other items stay saved and undeployed, the
        identical rerun resends only the refused item and fails again while the refusal lasts, then converges."""
        refusal = "Invalid Interfaces in leaf-12. The following interfaces are not in a valid host or secondary trunk mode: Ethernet1/9"
        self.ndfc.refuse[("pv-community", SN["leaf12"])] = refusal
        config = [{"net_name": "reg-l2", "net_id": 30101, "vlan_id": 2101, "is_l2only": True,
                   "attach": [{"ip_address": IP["leaf13"]}, {"ip_address": IP["leaf14"]}]}]
        config += self.family(isolated_attach=("leaf11",), community_attach=("leaf12",))
        for attempt in (1, 2):
            with self.subTest(attempt=attempt):
                result = self.run_module("merged", config, failed=True)
                self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
                self.assertEqual(result["msg"]["FAILED_ITEMS"], [{"pv-community-[PVL0000012/leaf-12]": refusal}])
                self.assertFalse([path for method, path, body in self.ndfc.writes() if "deploy" in path], "no deploy after a refusal")
                self.assertEqual(self.ndfc.writes()[-1][1], ATTACH, "the refused POST is the last write")
                attachments = result["pvlan_state"]["attachments"]
                self.assertEqual(
                    sorted((name, row["switchSerialNo"], row["lanAttachState"]) for name, rows in attachments.items() for row in rows),
                    [("pv-isolated", SN["leaf11"], "OUT-OF-SYNC"), ("pv-primary", SN["leaf11"], "OUT-OF-SYNC"),
                     ("reg-l2", SN["leaf13"], "OUT-OF-SYNC"), ("reg-l2", SN["leaf14"], "OUT-OF-SYNC")],
                )
                self.assertEqual(self.ndfc.status("pv-community"), "NA")
        self.assertEqual(self.attach_items(), [("pv-community", SN["leaf12"], True)], "the rerun sends only the refused item")

        del self.ndfc.refuse[("pv-community", SN["leaf12"])]
        result = self.run_module("merged", config)
        self.assertTrue(result["changed"])
        self.assertEqual(self.attach_items(), [("pv-community", SN["leaf12"], True)])
        for name in ("reg-l2", "pv-isolated", "pv-community", "pv-primary"):
            self.assertNotIn(self.ndfc.status(name), ("OUT-OF-SYNC", "PENDING"), name)
        self.assertFalse(self.run_module("merged", config)["changed"])

    def test_failure_delete_rerun(self):
        """A refused DELETE stops the removal before the primary; the identical rerun removes the rest
        (fake deploy model)."""
        self.seed_family(isolated_on=("leaf11",), community_on=("leaf12",))
        self.ndfc.fail_network[("DELETE", "pv-community")] = bad("DELETE", NETS + "/pv-community", "simulated controller error")
        config = [{"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}]
        result = self.run_module("deleted", config, failed=True)
        self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
        self.assertEqual(result["pvlan_state"]["networks"]["pv-isolated"], "absent")
        self.assertEqual(result["pvlan_state"]["attachments"], {})
        self.assertEqual(sorted(self.ndfc.networks), ["pv-community", "pv-primary"])
        self.assertNotIn(NETS + "/pv-primary", [path for method, path, body in self.ndfc.writes() if method == "DELETE"])

        result = self.run_module("deleted", config)
        self.assertTrue(result["changed"])
        self.assertEqual([path for method, path, body in self.ndfc.writes()], [NETS + "/pv-community", NETS + "/pv-primary"])
        self.assertEqual(self.ndfc.networks, {})
        self.assertFalse(self.run_module("deleted", config)["changed"])

    def test_failure_detach_refusal_during_delete(self):
        """A detach refused inside HTTP 200 stops the delete before any deploy or DELETE; the other detach of
        the same POST stays saved."""
        self.seed_family(isolated_on=("leaf11",), community_on=("leaf12",))
        self.ndfc.refuse[("pv-community", SN["leaf12"])] = "Detach is not allowed (simulated)"
        config = [{"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}]
        result = self.run_module("deleted", config, failed=True)
        self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
        self.assertEqual(result["msg"]["FAILED_ITEMS"], [{"pv-community-[PVL0000012/leaf-12]": "Detach is not allowed (simulated)"}])
        self.assertEqual([method for method, path, body in self.ndfc.writes()], ["POST"])
        self.assertEqual(sorted(self.ndfc.networks), ["pv-community", "pv-isolated", "pv-primary"])
        self.assertEqual((self.ndfc.rows[("pv-isolated", SN["leaf11"])]["state"], self.ndfc.rows[("pv-community", SN["leaf12"])]["state"]),
                         ("PENDING", "DEPLOYED"))

    def test_failure_state_read_errors(self):
        """A failed or malformed state read leaves that part unknown and is reported apart from the original
        failure; no network is reported absent without a valid network list read."""
        refusal = "Invalid Interfaces (simulated)"
        config = self.family(isolated_attach=("leaf11",), community_attach=("leaf12",))
        attach_read = ATTACH + "?network-names=pv-community,pv-isolated,pv-primary"
        cases = (
            # (injected read, networks known), the first network list read belongs to the request itself
            (("GET", NETS, bad("GET", NETS, "simulated read error"), 1), False),
            (("GET", NETS, ok("GET", NETS, {"message": "unexpected shape"}), 1), False),
            (("GET", attach_read, bad("GET", ATTACH, "simulated read error")), True),
            (("GET", attach_read, ok("GET", ATTACH, {"message": "unexpected shape"})), True),
        )
        expected_networks = {
            "pv-primary": {"networkId": 30010, "type": "Primary", "primaryNetworkId": -1, "networkStatus": "OUT-OF-SYNC"},
            "pv-isolated": {"networkId": 30011, "type": "Isolated", "primaryNetworkId": 30010, "networkStatus": "OUT-OF-SYNC"},
            "pv-community": {"networkId": 30012, "type": "Community", "primaryNetworkId": 30010, "networkStatus": "NA"},
        }
        for index, (inject, networks_known) in enumerate(cases):
            with self.subTest(read=index):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.ndfc.refuse[("pv-community", SN["leaf12"])] = refusal
                self.ndfc.inject.append(inject)
                result = self.run_module("merged", config, failed=True)
                self.assertEqual(self.ndfc.inject, [], "the injected read was consumed by the state read")
                self.assertEqual(result["msg"]["FAILED_ITEMS"], [{"pv-community-[PVL0000012/leaf-12]": refusal}], "original failure kept")
                state = result["pvlan_state"]
                self.assertIn("RETURN_CODE", state["read_error"])
                self.assertEqual(state["networks"], expected_networks if networks_known else None)
                self.assertIsNone(state["attachments"])
                self.assertEqual(result["acknowledged_writes"][-1]["refused_items"], [{"pv-community-[PVL0000012/leaf-12]": refusal}])
                self.assertEqual([write["method"] for write in result["acknowledged_writes"]], ["POST", "POST", "POST", "POST"])

    def test_failure_mixed_destructive_partial(self):
        """Mixed delete, one PVLAN DELETE refused: the regular deletion already sent is reported as an
        acknowledged write, the state read shows what remains, nothing is restored, and the next identical
        run removes the rest."""
        self.ndfc.seed("regular", "reg-old", 30101, 2101)
        self.seed_family()
        self.ndfc.fail_network[("DELETE", "pv-community")] = bad("DELETE", NETS + "/pv-community", "simulated controller error")
        config = [{"net_name": "reg-old"}, {"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}]
        result = self.run_module("deleted", config, failed=True)
        self.assertIn("acknowledged writes remain applied", result["msg"]["ROLLBACK_RESULT"])
        self.assertEqual(
            [(write["method"], write["path"]) for write in result["acknowledged_writes"]],
            [("DELETE", REST + "/top-down/fabrics/" + FABRIC + "/bulk-delete/networks?network-names=reg-old"), ("DELETE", NETS + "/pv-isolated")],
        )
        state = result["pvlan_state"]
        self.assertNotIn("read_error", state)
        self.assertEqual((state["networks"]["reg-old"], state["networks"]["pv-isolated"]), ("absent", "absent"))
        self.assertEqual((state["networks"]["pv-community"]["type"], state["networks"]["pv-primary"]["type"]), ("Community", "Primary"))
        self.assertEqual(sorted(self.ndfc.networks), ["pv-community", "pv-primary"])
        self.assertFalse([request for request in self.ndfc.writes() if request[0] in ("POST", "PUT")], "nothing is restored")

        result = self.run_module("deleted", config)
        self.assertTrue(result["changed"])
        self.assertEqual([path for method, path, body in self.ndfc.writes()], [NETS + "/pv-community", NETS + "/pv-primary"])
        self.assertFalse(self.run_module("deleted", config)["changed"])

    VLAN_POOL = "vlanUsageType=TOP_DOWN_NETWORK_VLAN"

    def test_failure_report_after_write_exits(self):
        """Exits that follow writes report through the PVLAN failure output: a failed autogenerated VLAN read
        after a regular network was deleted, and a malformed attachment read while waiting to delete. The
        original error stays in msg. Regular-only requests keep the plain message."""
        bulk_delete = REST + "/top-down/fabrics/" + FABRIC + "/bulk-delete/networks?network-names=reg-old"
        vlan_error = bad("GET", REST + "/resource-manager/vlan/" + FABRIC + "?" + self.VLAN_POOL, "simulated vlan pool error")
        for pvlan in (True, False):
            with self.subTest(case="autogenerated vlan", pvlan=pvlan):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.ndfc.seed("regular", "reg-old", 30101, 2101)
                self.ndfc.inject.append(("GET", self.VLAN_POOL, vlan_error))
                config = [{"net_name": "reg-new", "net_id": 30150, "is_l2only": True}] + (self.family()[2:] if pvlan else [])
                result = self.run_module("overridden", config, failed=True)
                self.assertEqual([method for method, path, body in self.ndfc.writes()], ["DELETE"])
                if not pvlan:
                    self.assertEqual(sorted(result), ["failed", "msg"])
                    self.assertIn("Failure getting autogenerated vlan_id", result["msg"])
                    continue
                self.assertIn("Failure getting autogenerated vlan_id", result["msg"]["DATA"])
                self.assertIn("simulated vlan pool error", result["msg"]["DATA"])
                self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
                self.assertEqual(result["acknowledged_writes"],
                                 [{"method": "DELETE", "path": bulk_delete, "return_code": 200, "outcome": "acknowledged"}])
                state = result["pvlan_state"]
                self.assertNotIn("read_error", state)
                self.assertEqual((state["networks"]["reg-old"], state["networks"]["reg-new"], state["networks"]["pv-primary"]),
                                 ("absent", "absent", "absent"))

        for label, reply, text in (("dict body", ok("GET", ATTACH, {"unexpected": "shape"}), "Unexpected DATA while waiting"),
                                   ("non-dict response", "unexpected text", "Unexpected response while waiting")):
            for pvlan in (True, False):
                with self.subTest(case=label, pvlan=pvlan):
                    self.ndfc.networks.clear()
                    self.ndfc.rows.clear()
                    if pvlan:
                        self.seed_family(isolated_on=("leaf11",))
                        name = "pv-isolated"
                    else:
                        self.ndfc.seed("regular", "reg-l2", 30101, 2101)
                        self.ndfc.attach("reg-l2", "leaf11")
                        name = "reg-l2"
                    # The read of the request lets the first attachment GET through; the wait poll gets the reply.
                    self.ndfc.inject.append(("GET", "attachments?network-names=" + name, reply, 1))
                    result = self.run_module("deleted", [{"net_name": name}], failed=True)
                    self.assertEqual([method for method, path, body in self.ndfc.writes() if method == "DELETE"], [])
                    if not pvlan:
                        self.assertEqual(sorted(result), ["failed", "msg"])
                        self.assertIn(text, result["msg"])
                        continue
                    self.assertIn(text, result["msg"]["DATA"])
                    self.assertEqual(
                        [(write["method"], write["path"], write["outcome"]) for write in result["acknowledged_writes"]],
                        [("POST", ATTACH, "acknowledged"), ("POST", self.CONFIG_DEPLOY + SN["leaf11"] + "?forceShowRun=false", "acknowledged")],
                    )
                    self.assertNotIn("read_error", result["pvlan_state"])
                    self.assertEqual(result["pvlan_state"]["networks"]["pv-isolated"]["type"], "Isolated")

    def test_acknowledged_writes_outcome(self):
        """Each acknowledged write states the outcome the module judged: a 200 with an ERROR key is listed as
        failed with its error text, after the successful writes before it, and an attachment POST with refused
        items keeps them under refused_items."""
        error = {"RETURN_CODE": 200, "METHOD": "POST", "MESSAGE": "OK", "REQUEST_PATH": NETS, "DATA": {}, "ERROR": "simulated body-level error"}
        self.ndfc.inject.append(("POST", NETS, error))
        config = [{"net_name": "reg-new", "net_id": 30150, "vlan_id": 2150, "is_l2only": True}] + self.family()
        result = self.run_module("merged", config, failed=True)
        self.assertEqual(result["msg"]["ERROR"], "simulated body-level error")
        self.assertEqual(result["acknowledged_writes"], [
            {"method": "POST", "path": REST + "/top-down/bulk-create/networks", "return_code": 200, "outcome": "acknowledged"},
            {"method": "POST", "path": NETS, "return_code": 200, "outcome": "failed", "error": "simulated body-level error"},
        ])
        self.assertEqual(sorted(self.ndfc.networks), ["reg-new"])

        self.ndfc.networks.clear()
        self.seed_family(isolated_on=("leaf11",))
        self.ndfc.refuse[("pv-community", SN["leaf12"])] = "Invalid Interfaces (simulated)"
        result = self.run_module("merged", [{"net_name": "pv-community", "is_l2only": True, "attach": [{"ip_address": IP["leaf12"]}]}], failed=True)
        self.assertEqual(result["acknowledged_writes"], [{
            "method": "POST", "path": ATTACH, "return_code": 200, "outcome": "items_refused",
            "refused_items": [{"pv-community-[PVL0000012/leaf-12]": "Invalid Interfaces (simulated)"}],
        }])

        # 200 OK with an error text in a string DATA: the module fails the run, and the entry says failed.
        self.ndfc.refuse.clear()
        self.ndfc.inject.append(("POST", ATTACH, {"RETURN_CODE": 200, "METHOD": "POST", "MESSAGE": "OK", "REQUEST_PATH": ATTACH,
                                                  "DATA": "Invalid interfaces supplied"}))
        result = self.run_module("merged", [{"net_name": "pv-community", "is_l2only": True, "attach": [{"ip_address": IP["leaf12"]}]}], failed=True)
        self.assertEqual(result["msg"]["DATA"], "Invalid interfaces supplied")
        self.assertEqual(result["acknowledged_writes"], [
            {"method": "POST", "path": ATTACH, "return_code": 200, "outcome": "failed", "error": "Invalid interfaces supplied"},
        ])
        self.assertEqual([method for method, path, body in self.ndfc.writes()], ["POST"], "no write after the failure")

    def test_delete_attachments_not_ready_fails(self):
        """A delete whose attachments never become ready fails and deletes nothing, instead of reporting success."""
        self.seed_family(isolated_on=("leaf11",))
        self.ndfc.stuck.add(("pv-isolated", SN["leaf11"]))
        result = self.run_module("deleted", [{"net_name": "pv-isolated"}], failed=True)
        self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
        self.assertIn("networks pv-isolated did not reach a state ready for deletion", result["msg"]["DATA"])
        self.assertEqual([path for method, path, body in self.ndfc.writes() if method == "DELETE"], [])
        self.assertEqual(sorted(self.ndfc.networks), ["pv-community", "pv-isolated", "pv-primary"])
        self.assertEqual(result["pvlan_state"]["attachments"]["pv-isolated"][0]["lanAttachState"], "PENDING")

    # ----- removal lifecycle -------------------------------------------------

    CONFIG_DEPLOY = REST + "/control/fabrics/" + FABRIC + "/config-deploy/"
    NETWORK_DEPLOY = REST + "/top-down/networks/deploy"

    def deploys(self):
        """Return the deploy requests sent: switch lists for config-deploy, bodies for network deploys."""
        sent = []
        for method, path, body in self.ndfc.writes():
            if path.startswith(self.CONFIG_DEPLOY):
                sent.append(sorted(path[len(self.CONFIG_DEPLOY):].split("?", 1)[0].split(",")))
            elif path == self.NETWORK_DEPLOY:
                sent.append({serial: sorted(names.split(",")) for serial, names in body.items()})
        return sent

    def saved_isolated_removal(self, preview=False):
        """Family deployed (isolated on leaf11, community on leaf12); replaced with deploy false saves the
        removal of the isolated attachment, which also withdraws the implicit primary on leaf11."""
        self.seed_family(isolated_on=("leaf11",), community_on=("leaf12",))
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        config = [
            {"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": mcast, "attach": []},
            {"net_name": "pv-community", "vlan_id": 2433, "is_l2only": True, "multicast_group_address": mcast,
             "attach": [{"ip_address": IP["leaf12"]}]},
            {"net_name": "pv-primary", "vlan_id": 2431, "is_l2only": True, "multicast_group_address": mcast, "attach": []},
        ]
        self.assertTrue(self.run_module("replaced", [dict(entry, deploy=False) for entry in config])["changed"])
        self.assertEqual(self.deploys(), [])
        for key in (("pv-isolated", SN["leaf11"]), ("pv-primary", SN["leaf11"])):
            self.assertEqual((self.ndfc.rows[key]["attached"], self.ndfc.rows[key]["state"]), (False, "PENDING"))
            if preview:
                self.ndfc.rows[key]["state"] = "OUT-OF-SYNC"
        return config

    def test_saved_removal_deployed_by_later_run(self):
        """A removal saved with deploy false is deployed by the next run with deploy true, in merged, replaced
        and overridden, with the rows PENDING or OUT-OF-SYNC. Only that switch is deployed; the primary that
        NDFC withdrew with the secondary is named in resource mode. A run with deploy false sends nothing, and
        the run after the deploy is a no-op."""
        for state in ("merged", "replaced", "overridden"):
            for preview in (False, True):
                for mode in (None, "resource"):
                    with self.subTest(state=state, preview=preview, mode=mode):
                        self.ndfc.networks.clear()
                        self.ndfc.rows.clear()
                        config = self.saved_isolated_removal(preview)
                        result = self.run_module(state, [dict(entry, deploy=False) for entry in config], deploy_mode=mode)
                        self.assertFalse(result["changed"], result)
                        self.assert_no_writes()

                        check = self.run_module(state, [dict(entry, deploy=True) for entry in config], deploy_mode=mode, check_mode=True)
                        self.assertTrue(check["changed"])
                        self.assert_no_writes()

                        result = self.run_module(state, [dict(entry, deploy=True) for entry in config], deploy_mode=mode)
                        self.assertTrue(result["changed"])
                        self.assertEqual([method for method, path, body in self.ndfc.writes()], ["POST"], "a deploy only, no detach")
                        if mode:
                            self.assertEqual(self.deploys(), [{SN["leaf11"]: ["pv-isolated", "pv-primary"]}])
                        else:
                            self.assertEqual(self.deploys(), [[SN["leaf11"]]])
                        self.assertNotIn(("pv-isolated", SN["leaf11"]), self.ndfc.rows)
                        self.assertNotIn(("pv-primary", SN["leaf11"]), self.ndfc.rows)
                        self.assertEqual(
                            [(entry["net_name"], entry["switch"], entry["lanAttachState"]) for entry in result["pvlan_deploy_plan"]],
                            [(name, IP["leaf11"] + " (" + SN["leaf11"] + ")", "OUT-OF-SYNC" if preview else "PENDING")
                             for name in ("pv-isolated", "pv-primary")],
                        )
                        self.assertEqual(check["pvlan_deploy_plan"], result["pvlan_deploy_plan"])
                        self.assertFalse(self.run_module(state, [dict(entry, deploy=True) for entry in config], deploy_mode=mode)["changed"])

    def test_saved_removal_plan_names_family(self):
        """Check mode for a saved removal of a secondary also lists the primary that was withdrawn with it, when
        the request does not name the primary; the run then removes both rows with one deploy."""
        config = self.saved_isolated_removal()
        isolated = [dict(entry, deploy=True) for entry in config if entry["net_name"] == "pv-isolated"]
        check = self.run_module("merged", isolated, check_mode=True)
        self.assert_no_writes()
        self.assertEqual([(entry["net_name"], entry["lanAttachState"]) for entry in check["pvlan_deploy_plan"]],
                         [("pv-isolated", "PENDING"), ("pv-primary", "PENDING")])
        self.assertTrue(self.run_module("merged", isolated, deploy_mode="resource")["changed"])
        self.assertEqual(self.deploys(), [{SN["leaf11"]: ["pv-isolated", "pv-primary"]}])
        self.assertEqual(sorted(self.ndfc.rows), [("pv-community", SN["leaf12"]), ("pv-primary", SN["leaf12"])])

    def test_removal_deployed_in_same_run(self):
        """replaced with deploy true deploys the switch it detaches a PVLAN network from, not only the
        switches that stay attached; the primary withdrawn with the secondary is named in resource mode."""
        for mode in (None, "resource"):
            with self.subTest(mode=mode):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.seed_family(isolated_on=("leaf11",), community_on=("leaf12",))
                mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
                config = [{"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": mcast, "attach": []}]
                self.assertTrue(self.run_module("replaced", config, deploy_mode=mode)["changed"])
                self.assertEqual(self.attach_items(), [("pv-isolated", SN["leaf11"], False)])
                self.assertEqual(self.deploys(), [{SN["leaf11"]: ["pv-isolated", "pv-primary"]}] if mode else [[SN["leaf11"]]])
                self.assertEqual(sorted(self.ndfc.rows), [("pv-community", SN["leaf12"]), ("pv-primary", SN["leaf12"])])
                self.assertFalse(self.run_module("replaced", config, deploy_mode=mode)["changed"])

    def test_mixed_replaced_removal_regular_unchanged(self):
        """replaced removing a regular attachment and a PVLAN attachment in one run: only the PVLAN removal is
        deployed by the module; the regular network keeps the inherited targets (none when no switch stays
        attached) and its rows stay saved."""
        for mode in (None, "resource"):
            with self.subTest(mode=mode):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.seed_family(isolated_on=("leaf11",))
                self.ndfc.seed("regular", "reg-l2", 30101, 2101)
                self.ndfc.attach("reg-l2", "leaf13")
                self.ndfc.attach("reg-l2", "leaf14")
                mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
                reg_mcast = json.loads(self.ndfc.networks["reg-l2"]["networkTemplateConfig"])["mcastGroup"]
                config = [
                    {"net_name": "reg-l2", "vlan_id": 2101, "is_l2only": True, "multicast_group_address": reg_mcast, "attach": []},
                    {"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": mcast, "attach": []},
                ]
                self.assertTrue(self.run_module("replaced", config, deploy_mode=mode)["changed"])
                self.assertEqual(sorted(self.attach_items()), sorted([("pv-isolated", SN["leaf11"], False), ("reg-l2", SN["leaf13"], False),
                                                                      ("reg-l2", SN["leaf14"], False)]))
                self.assertEqual(self.deploys(), [{SN["leaf11"]: ["pv-isolated", "pv-primary"]}] if mode else [[SN["leaf11"]]])
                self.assertEqual({self.ndfc.rows[("reg-l2", SN[name])]["state"] for name in ("leaf13", "leaf14")}, {"PENDING"})

    def two_families_saved_removal(self):
        """Family pv saved for removal on leaf11 (all rows PENDING), family pw deployed on leaf12, NA rows on
        leaf13 and leaf14."""
        self.seed_family(isolated_on=("leaf11",), community_on=("leaf11",))
        self.ndfc.seed("primary_l2", "pw-primary", 30020, 2441)
        self.ndfc.seed("isolated", "pw-isolated", 30021, 2442, primary="pw-primary")
        self.ndfc.attach("pw-isolated", "leaf12")
        for key in [key for key in self.ndfc.rows if key[0].startswith("pv-")]:
            self.ndfc.rows[key].update({"attached": False, "state": "PENDING", "explicit": False})
        return [{"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}]

    def test_delete_saved_removal_targets(self):
        """deleted after a saved removal deploys only the switch that holds it: no other family's switch and no
        switch with only NA rows. No detach is resent for rows already detached (the implicit primary's would be
        refused). The other family is untouched; check mode reports the same rows."""
        for mode in (None, "resource"):
            with self.subTest(mode=mode):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                config = self.two_families_saved_removal()
                check = self.run_module("deleted", config, check_mode=True, deploy_mode=mode)
                self.assert_no_writes()
                self.assertEqual(sorted((entry["net_name"], entry["lanAttachState"]) for entry in check["pvlan_deploy_plan"]),
                                 [("pv-community", "PENDING"), ("pv-isolated", "PENDING"), ("pv-primary", "PENDING")])
                self.assertEqual({entry["switch"] for entry in check["pvlan_deploy_plan"]}, {IP["leaf11"] + " (" + SN["leaf11"] + ")"})

                self.assertTrue(self.run_module("deleted", config, deploy_mode=mode)["changed"])
                self.assertEqual(self.attach_items(), [])
                self.assertEqual(self.deploys(), [{SN["leaf11"]: ["pv-community", "pv-isolated", "pv-primary"]}] if mode else [[SN["leaf11"]]])
                self.assertEqual(sorted(self.ndfc.networks), ["pw-isolated", "pw-primary"])
                self.assertEqual(self.ndfc.rows[("pw-isolated", SN["leaf12"])]["state"], "DEPLOYED")
                self.assertFalse(self.run_module("deleted", config, deploy_mode=mode)["changed"])

    def test_delete_attached_and_saved_rows_one_deploy(self):
        """A PVLAN network attached on one switch and holding a saved removal on another is undeployed on both
        with one deploy before the delete; the switches with NA rows are not deployed."""
        for mode in (None, "resource"):
            with self.subTest(mode=mode):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.seed_family(community_on=("leaf11", "leaf12"))
                self.ndfc.rows[("pv-community", SN["leaf12"])].update({"attached": False, "state": "PENDING"})
                self.ndfc.rows[("pv-primary", SN["leaf12"])].update({"attached": False, "state": "PENDING"})
                self.assertTrue(self.run_module("deleted", [{"net_name": "pv-community"}], deploy_mode=mode)["changed"])
                self.assertEqual(self.attach_items(), [("pv-community", SN["leaf11"], False)])
                if mode:
                    self.assertEqual(self.deploys(), [{SN["leaf11"]: ["pv-community", "pv-primary"], SN["leaf12"]: ["pv-community", "pv-primary"]}])
                else:
                    self.assertEqual(self.deploys(), [[SN["leaf11"], SN["leaf12"]]])
                self.assertNotIn("pv-community", self.ndfc.networks)
                self.assertEqual(self.ndfc.rows, {})

    def test_delete_detached_row_in_other_state_is_not_ready(self):
        """A detached row in a state that is neither NA nor a saved removal (here IN PROGRESS) is not ready for
        deletion: the run waits, fails without a DELETE and does not deploy it."""
        self.seed_family(isolated_on=("leaf11",))
        key = ("pv-isolated", SN["leaf11"])
        self.ndfc.rows[key].update({"attached": False, "state": "IN PROGRESS", "explicit": False})
        self.ndfc.stuck.add(key)
        result = self.run_module("deleted", [{"net_name": "pv-isolated"}], failed=True)
        self.assertIn("did not reach a state ready for deletion", result["msg"]["DATA"])
        self.assertEqual([request for request in self.ndfc.writes() if request[0] == "DELETE"], [])
        self.assertEqual(self.deploys(), [])
        self.assertIn("pv-isolated", self.ndfc.networks)

    def test_delete_primary_histories(self):
        """Deleting a deployed family: an explicit primary is detached after its secondaries, an implicit one is
        not (it follows its last secondary). Both histories deploy the same switch and delete in the same order."""
        for explicit in (True, False):
            with self.subTest(explicit=explicit):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.history(explicit)
                self.ndfc.deploy(set(self.ndfc.rows))
                config = [{"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}]
                result = self.run_module("deleted", config)
                self.assertTrue(result["changed"])
                expected = [("pv-isolated", SN["leaf11"], False)] + ([("pv-primary", SN["leaf11"], False)] if explicit else [])
                self.assertEqual(self.attach_items(), expected)
                self.assertEqual(self.deploys(), [[SN["leaf11"]]])
                self.assertEqual([path.rsplit("/", 1)[1] for method, path, body in self.ndfc.writes() if method == "DELETE"],
                                 ["pv-isolated", "pv-community", "pv-primary"])
                self.assertEqual(self.ndfc.networks, {})

    def test_delete_out_of_sync_is_not_ready(self):
        """Rows OUT-OF-SYNC after a preview still hold configuration: deleted deploys them and deletes only when
        every row is NA. When the deploy does not settle them, the run fails without a DELETE, and the identical
        run after they settle deploys once more and deletes."""
        self.seed_family(isolated_on=("leaf11",), community_on=("leaf11",))
        for key in list(self.ndfc.rows):
            self.ndfc.rows[key].update({"attached": False, "state": "OUT-OF-SYNC", "explicit": False})
            self.ndfc.stuck.add(key)
        config = [{"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}]
        result = self.run_module("deleted", config, failed=True)
        self.assertIn("did not reach a state ready for deletion", result["msg"]["DATA"])
        self.assertEqual(self.deploys(), [[SN["leaf11"]]], "one deploy per row and run")
        self.assertEqual([request for request in self.ndfc.writes() if request[0] == "DELETE"], [])
        self.assertEqual({row["lanAttachState"] for rows in result["pvlan_state"]["attachments"].values() for row in rows
                          if row["switchSerialNo"] == SN["leaf11"]}, {"OUT-OF-SYNC"})

        self.ndfc.stuck.clear()
        self.assertTrue(self.run_module("deleted", config)["changed"])
        self.assertEqual(self.deploys(), [[SN["leaf11"]]])
        self.assertEqual(self.ndfc.networks, {})

    def test_delete_network_status_out_of_sync_is_not_ready(self):
        """When every attachment is NA but the network still reads OUT-OF-SYNC, a PVLAN network is not deleted."""
        self.seed_family()
        self.ndfc.status_override["pv-community"] = "OUT-OF-SYNC"
        result = self.run_module("deleted", [{"net_name": "pv-community"}], failed=True)
        self.assertIn("Timeout waiting for networks to be ready for deletion", result["msg"]["DATA"])
        self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
        self.assertEqual(self.ndfc.writes(), [])
        self.assertIn("pv-community", self.ndfc.networks)

    def test_delete_retry_detach_ordered_and_checked(self):
        """A row still attached after the detach step is detached again through the ordered, item-checked path,
        and the removal that detach saves is deployed again. A refusal of that retry fails the run without a
        DELETE."""
        for refused in (False, True):
            with self.subTest(refused=refused):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.ndfc.refuse.clear()
                self.seed_family(isolated_on=("leaf11",), community_on=("leaf12",))
                # The first detach POST is acknowledged without effect.
                self.ndfc.inject.append(("POST", ATTACH, ok("POST", ATTACH, {"pv-isolated-[PVL0000011/leaf-11]": "SUCCESS"})))
                if refused:
                    self.ndfc.refuse[("pv-isolated", SN["leaf11"])] = "Detach is not allowed (simulated)"
                result = self.run_module("deleted", [{"net_name": "pv-isolated"}], failed=refused)
                self.assertEqual(self.attach_items(), [("pv-isolated", SN["leaf11"], False)] * 2)
                if refused:
                    self.assertEqual(result["msg"]["FAILED_ITEMS"], [{"pv-isolated-[PVL0000011/leaf-11]": "Detach is not allowed (simulated)"}])
                    self.assertEqual(self.deploys(), [[SN["leaf11"]]])
                    self.assertEqual([request for request in self.ndfc.writes() if request[0] == "DELETE"], [])
                    self.assertIn("pv-isolated", self.ndfc.networks)
                else:
                    self.assertTrue(result["changed"])
                    self.assertEqual(self.deploys(), [[SN["leaf11"]], [SN["leaf11"]]])
                    self.assertNotIn("pv-isolated", self.ndfc.networks)
                    self.assertEqual(sorted(self.ndfc.rows), [("pv-community", SN["leaf12"]), ("pv-primary", SN["leaf12"])])

    def test_mixed_delete_regular_targets_unchanged(self):
        """Mixed delete after saved removals: the regular network keeps the inherited deploy targets, the PVLAN
        family is deployed only where it holds a saved removal, and both are deleted."""
        for mode in (None, "resource"):
            with self.subTest(mode=mode):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                config = self.two_families_saved_removal()
                self.ndfc.seed("regular", "reg-l2", 30101, 2101)
                self.ndfc.attach("reg-l2", "leaf13")
                self.ndfc.attach("reg-l2", "leaf14")
                for serial in (SN["leaf13"], SN["leaf14"]):
                    self.ndfc.rows[("reg-l2", serial)].update({"attached": False, "state": "PENDING"})
                self.assertTrue(self.run_module("deleted", config + [{"net_name": "reg-l2"}], deploy_mode=mode)["changed"])
                regular_detach = [item for item in self.attach_items() if item[0] == "reg-l2"]
                self.assertEqual(regular_detach, [("reg-l2", SN["leaf13"], False), ("reg-l2", SN["leaf14"], False)], "inherited re-detach")
                if mode:
                    self.assertEqual(self.deploys(), [{SN["leaf11"]: ["pv-community", "pv-isolated", "pv-primary"]},
                                                      {SN["leaf13"]: ["reg-l2"], SN["leaf14"]: ["reg-l2"]}])
                else:
                    self.assertEqual(self.deploys(), [[SN["leaf11"]], sorted(SN.values())], "regular keeps every switch (inherited)")
                self.assertEqual(sorted(self.ndfc.networks), ["pw-isolated", "pw-primary"])

    # ----- deploy and saved state --------------------------------------------

    def test_saved_then_deploy(self):
        """Deploy false saves the attachment; repeat is a no-op; deploy true deploys only."""
        saved = self.family(isolated_attach=("leaf11",), deploy=False)
        result = self.run_module("merged", saved)
        self.assertTrue(result["changed"])
        self.assertFalse([path for method, path, body in self.ndfc.requests if "deploy" in path])
        self.assertFalse(self.run_module("merged", saved)["changed"])
        deploy = self.family(isolated_attach=("leaf11",), deploy=True)
        result = self.run_module("merged", deploy)
        self.assertTrue(result["changed"])
        self.assertEqual([path for method, path, body in self.ndfc.writes()],
                         [REST + "/control/fabrics/" + FABRIC + "/config-deploy/" + SN["leaf11"] + "?forceShowRun=false"])

    def test_saved_detach_repeat(self):
        """A saved detach reads isLanAttached false / PENDING; the repeat is a no-op."""
        self.seed_family(isolated_on=("leaf11",))
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        config = [{"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": mcast, "attach": [], "deploy": False}]
        self.assertTrue(self.run_module("replaced", config)["changed"])
        self.assertEqual(self.ndfc.rows[("pv-isolated", SN["leaf11"])]["state"], "PENDING")
        self.assertFalse([path for method, path, body in self.ndfc.requests if "deploy" in path])
        self.assertFalse(self.run_module("replaced", config)["changed"])

    def test_mixed_deploy_choices(self):
        """Only networks with deploy true are deployed."""
        config = self.family(isolated_attach=("leaf11",), community_attach=("leaf12",))
        config[1]["deploy"] = False
        self.assertTrue(self.run_module("merged", config)["changed"])
        deploys = [path for method, path, body in self.ndfc.writes() if "config-deploy" in path]
        self.assertEqual(deploys, [REST + "/control/fabrics/" + FABRIC + "/config-deploy/" + SN["leaf11"] + "?forceShowRun=false"])

    def test_deploy_mode_resource_visible(self):
        """Resource mode names the attached secondary and the primary that NDFC added with it on that switch,
        because a network deploy changes only the networks it names. A family member already deployed there
        is not added."""
        self.assertTrue(self.run_module("merged", self.family(isolated_attach=("leaf11",)), deploy_mode="resource")["changed"])
        deploy = self.bodies("POST", REST + "/top-down/networks/deploy")
        self.assertEqual(len(deploy), 1)
        self.assertEqual(deploy[0][SN["leaf11"]].split(","), ["pv-isolated", "pv-primary"])
        self.assertEqual(self.ndfc.rows[("pv-primary", SN["leaf11"])]["state"], "DEPLOYED")

        self.assertTrue(self.run_module("merged", self.family(isolated_attach=("leaf11",), community_attach=("leaf11",)), deploy_mode="resource")["changed"])
        self.assertEqual(self.bodies("POST", REST + "/top-down/networks/deploy"), [{SN["leaf11"]: "pv-community"}])

    def test_check_mode_zero_writes(self):
        """Check mode sends no write and reports the PVLAN options in the diff."""
        result = self.run_module("merged", self.family(isolated_attach=("leaf11",)), check_mode=True)
        self.assertTrue(result["changed"])
        self.assert_no_writes()
        self.assertFalse([path for method, path, body in self.ndfc.requests if path.endswith("/netinfo") or "resource-manager" in path])
        diff = {entry["net_name"]: entry for entry in result["diff"]}
        self.assertEqual((diff["pv-isolated"]["pvlan_type"], diff["pv-isolated"]["pvlan_primary"]), ("isolated", "pv-primary"))
        self.assertEqual(diff["pv-primary"]["pvlan_type"], "primary")
        self.assertNotIn("pvlan_primary", diff["pv-primary"])
        for entry in diff.values():
            self.assertNotIn("type", entry)
            self.assertNotIn("primaryNetworkId", entry)
        self.assertEqual(self.ndfc.networks, {})

    def test_query_reports_family(self):
        """A routed network is present because query with config reads only VRF-scoped
        networks unless one of them exists (inherited behavior for every Layer 2 only network)."""
        self.ndfc.seed("regular", "reg-routed", 30100, 2100, vrf="VRF_A", isLayer2Only="false")
        self.seed_family(isolated_on=("leaf11",))
        result = self.run_module("query", [{"net_name": "pv-isolated"}])
        parent = result["response"][0]["parent"]
        self.assertEqual((parent["type"], parent["primaryNetworkId"]), ("Isolated", 30010))

    def test_query_layer2_family_without_routed_network(self):
        """Without any VRF-scoped network, query still returns the PVLAN networks it names. A regular Layer 2
        only network keeps the existing result in that case (not returned); with a routed network present,
        every named network is returned as before."""
        self.seed_family(isolated_on=("leaf11",))
        self.ndfc.seed("regular", "reg-l2", 30101, 2101)
        names = [{"net_name": name} for name in ("pv-primary", "pv-isolated", "pv-community", "reg-l2", "missing")]
        result = self.run_module("query", names)
        returned = {item["parent"]["networkName"]: item for item in result["response"]}
        self.assertEqual(sorted(returned), ["pv-community", "pv-isolated", "pv-primary"])
        self.assertEqual((returned["pv-isolated"]["parent"]["type"], returned["pv-isolated"]["parent"]["primaryNetworkId"]), ("Isolated", 30010))
        self.assertEqual([row["switchSerialNo"] for row in returned["pv-primary"]["attach"] if row["isLanAttached"]], [SN["leaf11"]])
        self.assert_no_writes()

        self.ndfc.seed("regular", "reg-routed", 30100, 2100, vrf="VRF_A", isLayer2Only="false")
        result = self.run_module("query", names)
        self.assertEqual(sorted(item["parent"]["networkName"] for item in result["response"]),
                         ["pv-community", "pv-isolated", "pv-primary", "reg-l2"])

    def test_action_plugin_path(self):
        """The action plugin forwards the PVLAN keys and its default deploy flag."""
        self.nd_support_version = {"RETURN_CODE": 200, "METHOD": "GET", "MESSAGE": "OK", "DATA": {"version": "12.6.0.267"}}
        network_data = loadPlaybookData("dcnm_network")
        self.fabric_associations = network_data.get("fabric_associations")
        self.multicluster_fabric_associations = network_data.get("multicluster_fabric_associations")
        set_module_args({"fabric": FABRIC, "state": "merged", "config": self.family(isolated_attach=("leaf11",))})
        result = self._execute_via_action_plugin(failed=False, changed=True)
        self.assertTrue(result["changed"], result)
        self.assertEqual(sorted(self.ndfc.networks), ["pv-community", "pv-isolated", "pv-primary"])
        self.assertTrue([path for method, path, body in self.ndfc.writes() if "config-deploy" in path])

    # ----- named ports -------------------------------------------------------
    #
    # Port fields of the sent items are compared with port_attach_items (accepted by NDFC 12.6 through the legacy
    # API). The item envelope differs from those hand-built bodies: no isAttached or torports, freeformConfig null
    # on a new attachment, instanceValues merged from the readback and vlan from the network.

    PORT_FIELDS = ("switchPorts", "detachSwitchPorts", "dot1QVlan", "untagged", "deployment", "extensionValues")

    def port_items(self, deployment=None):
        """(network, serial, switchPorts, detachSwitchPorts, deployment) of every attachment item sent, in order."""
        out = []
        for method, path, body in self.ndfc.requests:
            if method == "POST" and path == ATTACH:
                for entry in body:
                    for item in entry["lanAttachList"]:
                        if deployment is None or item["deployment"] is deployment:
                            out.append((entry["networkName"], item["serialNumber"], item.get("switchPorts"), item.get("detachSwitchPorts"), item["deployment"]))
        return out

    def port_posts(self):
        """Attachment POSTs as lists of (network, serial, switchPorts, detachSwitchPorts, deployment)."""
        posts = []
        for method, path, body in self.ndfc.requests:
            if method == "POST" and path == ATTACH:
                posts.append([(e["networkName"], i["serialNumber"], i.get("switchPorts"), i.get("detachSwitchPorts"), i["deployment"])
                              for e in body for i in e["lanAttachList"]])
        return posts

    def ports_on(self, name, switch):
        row = self.ndfc.rows.get((name, SN[switch]))
        return row["ports"] if row and row["attached"] else None

    def assert_port_fields(self, item, measured):
        expected = self.fixtures["port_attach_items"][measured]
        self.assertEqual({k: item.get(k) for k in self.PORT_FIELDS}, {k: expected.get(k) for k in self.PORT_FIELDS})

    def existing_net(self, name, vlan, attach=None):
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        entry = {"net_name": name, "vlan_id": vlan, "is_l2only": True, "multicast_group_address": mcast}
        if attach is not None:
            entry["attach"] = attach
        return entry

    @staticmethod
    def regular_l2(attach=None, **extra):
        entry = dict({"net_name": "reg-l2", "net_id": 30101, "vlan_id": 2101, "is_l2only": True}, **extra)
        if attach is not None:
            entry["attach"] = attach
        return entry

    def seed_regular_l2(self, on=None):
        self.ndfc.seed("regular", "reg-l2", 30101, 2101, isLayer2Only="true")["vrf"] = "NA"
        for switch, ports in (on or {}).items():
            self.ndfc.attach("reg-l2", switch, ports=ports)

    # regular networks: unchanged behavior

    def test_regular_ports_attach_and_repeat(self):
        """Ethernet, Po and a vPC with a different port-channel per peer; the repeat writes nothing."""
        config = [self.regular_l2([{"ip_address": IP["leaf11"], "ports": ["ethernet1/41", "port-channel541"]},
                                   {"ip_address": IP["leaf13"], "ports": ["Port-channel543"]},
                                   {"ip_address": IP["leaf14"], "ports": ["Port-channel544"]}])]
        self.assertTrue(self.run_module("merged", config)["changed"])
        self.assertEqual(sorted(item[1:3] for item in self.port_items()),
                         sorted([(SN["leaf11"], "Ethernet1/41,Port-channel541"), (SN["leaf13"], "Port-channel543"), (SN["leaf14"], "Port-channel544")]))
        self.assertFalse(self.run_module("merged", config)["changed"])
        self.assert_no_writes()

    def test_regular_port_changes(self):
        """merged adds only new ports; replaced sends the exact set; ports [] keeps the switch; an omitted switch is one
        detach item that still holds its ports; deleted detaches with the ports."""
        cases = (
            ("merged", {"leaf11": "Ethernet1/41"}, [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/42"]}], [(SN["leaf11"], "Ethernet1/42", "", True)]),
            ("replaced", {"leaf11": "Ethernet1/41,Ethernet1/42"}, [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/42"]}],
             [(SN["leaf11"], "", "Ethernet1/41", True)]),
            ("replaced", {"leaf11": "Ethernet1/41"}, [{"ip_address": IP["leaf11"]}], [(SN["leaf11"], "", "Ethernet1/41", True)]),
            ("replaced", {"leaf11": "Ethernet1/41", "leaf12": ""}, [{"ip_address": IP["leaf12"]}], [(SN["leaf11"], "Ethernet1/41", "", False)]),
        )
        for state, seeded, attach, items in cases:
            with self.subTest(state=state, seeded=seeded, attach=attach):
                self.ndfc.networks, self.ndfc.rows = {}, {}
                self.seed_regular_l2(seeded)
                self.run_module(state, [self.regular_l2(attach)])
                self.assertEqual([item[1:] for item in self.port_items()], items)
        self.ndfc.networks, self.ndfc.rows = {}, {}
        self.seed_regular_l2({"leaf11": "Ethernet1/41"})
        self.run_module("deleted", [{"net_name": "reg-l2"}])
        self.assertEqual(self.port_items(), [("reg-l2", SN["leaf11"], "Ethernet1/41", "", False)])

    def test_regular_vpc_one_peer_change_check_mode_and_deploy(self):
        """A one-peer port change re-sends the other peer without ports; check mode sends nothing; save then deploy."""
        self.seed_regular_l2({"leaf13": "Port-channel543", "leaf14": "Port-channel544"})
        config = [self.regular_l2([{"ip_address": IP["leaf13"], "ports": ["Port-channel543"]}, {"ip_address": IP["leaf14"], "ports": ["Port-channel545"]}])]
        self.assertTrue(self.run_module("replaced", config, check_mode=True)["changed"])
        self.assert_no_writes()
        self.run_module("replaced", config)
        self.assertEqual(sorted(i[1:4] for i in self.port_items()), sorted([(SN["leaf13"], "", ""), (SN["leaf14"], "Port-channel545", "Port-channel544")]))
        self.assertEqual(self.ports_on("reg-l2", "leaf13"), "Port-channel543")

        self.ndfc.networks, self.ndfc.rows = {}, {}
        saved = [self.regular_l2([{"ip_address": IP["leaf11"], "ports": ["Ethernet1/41"]}], deploy=False)]
        self.run_module("merged", saved)
        self.assertEqual([r for r in self.ndfc.writes() if "deploy" in r[1]], [])
        self.run_module("merged", [dict(saved[0], deploy=True)])
        self.assertEqual(self.bodies("POST", ATTACH), [])
        self.assertEqual(self.ndfc.rows[("reg-l2", SN["leaf11"])]["state"], "DEPLOYED")

    # PVLAN networks

    def test_ports_isolated_ethernet_host(self):
        """Isolated on an Ethernet host port: one item, the controller adds the primary; repeats write nothing."""
        self.seed_family()
        config = [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/41"]}])]
        self.assertTrue(self.run_module("merged", config)["changed"])
        self.assertEqual(self.port_items(), [("pv-isolated", SN["leaf11"], "Ethernet1/41", "", True)])
        self.assert_port_fields(self.bodies("POST", ATTACH)[0][0]["lanAttachList"][0], "ethernet_host")
        self.assertEqual(self.ndfc.attached("pv-primary"), [SN["leaf11"]])
        for state in ("merged", "replaced"):
            self.assertFalse(self.run_module(state, config)["changed"], state)

    def test_ports_community_port_channel(self):
        self.seed_family()
        config = [self.existing_net("pv-community", 2433, [{"ip_address": IP["leaf11"], "ports": ["port-channel541"]}])]
        self.assertTrue(self.run_module("merged", config)["changed"])
        self.assertEqual(self.port_items(), [("pv-community", SN["leaf11"], "Port-channel541", "", True)])
        self.assertFalse(self.run_module("replaced", config)["changed"])

    def test_ports_vpc_unequal_port_channels(self):
        """One POST, one item per vPC peer with its own port-channel number."""
        self.seed_family()
        config = [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf13"], "ports": ["Port-channel543"]},
                                                          {"ip_address": IP["leaf14"], "ports": ["Port-channel544"]}])]
        self.assertTrue(self.run_module("merged", config)["changed"])
        self.assertEqual(len(self.bodies("POST", ATTACH)), 1)
        sent = {item["serialNumber"]: item for item in self.bodies("POST", ATTACH)[0][0]["lanAttachList"]}
        self.assert_port_fields(sent[SN["leaf13"]], "vpc_peer1")
        self.assert_port_fields(sent[SN["leaf14"]], "vpc_peer2")
        for state in ("merged", "replaced"):
            self.assertFalse(self.run_module(state, config)["changed"], state)

    def test_ports_primary_promiscuous_order(self):
        """A primary port item is sent before secondary port items."""
        self.seed_family()
        config = [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/41"]}]),
                  self.existing_net("pv-primary", 2431, [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/44"]}])]
        self.assertTrue(self.run_module("merged", config)["changed"])
        self.assertEqual(self.port_posts(), [[("pv-primary", SN["leaf11"], "Ethernet1/44", "", True)],
                                             [("pv-isolated", SN["leaf11"], "Ethernet1/41", "", True)]])
        self.assertFalse(self.run_module("merged", config)["changed"])

    def test_ports_without_switch_attach(self):
        self.seed_family()
        self.run_module("merged", [self.existing_net("pv-community", 2433, [{"ip_address": IP["leaf12"], "ports": ["Ethernet1/41"]}])])
        self.assertEqual(self.port_items(), [("pv-community", SN["leaf12"], "Ethernet1/41", "", True)])
        self.assert_port_fields(self.bodies("POST", ATTACH)[0][0]["lanAttachList"][0], "without_switch_attach")

    def test_ports_port_detach_keeps_switch_and_primary(self):
        """Removing one port or every port of a switch sends a port detach; the switch row and the implicit primary stay."""
        for kept, want in ((["Ethernet1/42"], ("", "Ethernet1/41")), ([], ("", "Ethernet1/41,Ethernet1/42"))):
            with self.subTest(kept=kept):
                self.ndfc.networks, self.ndfc.rows = {}, {}
                self.seed_family()
                self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41,Ethernet1/42")
                attach = {"ip_address": IP["leaf11"]}
                if kept:
                    attach["ports"] = kept
                self.run_module("replaced", [self.existing_net("pv-isolated", 2432, [attach])])
                items = self.port_items()
                self.assertEqual(len(items), 1)
                self.assertEqual((items[0][2], sorted(items[0][3].split(",")), items[0][4]), (want[0], sorted(want[1].split(",")), True))
                self.assertEqual(self.ndfc.attached("pv-isolated"), [SN["leaf11"]])
                self.assertEqual(self.ndfc.attached("pv-primary"), [SN["leaf11"]])
        self.assert_port_fields(dict(self.bodies("POST", ATTACH)[0][0]["lanAttachList"][0], detachSwitchPorts="Ethernet1/41"), "port_detach")

    def test_ports_switch_detach_sends_port_detach_first(self):
        """A switch detach of a row that holds a port: a port detach POST, then the switch detach without ports."""
        self.seed_family()
        self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41")
        self.ndfc.attach("pv-isolated", "leaf12")
        # The primary is listed on leaf-12 only, so the family rule does not keep the leaf-11 row.
        self.run_module("replaced", [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf12"]}]),
                                     self.existing_net("pv-primary", 2431, [{"ip_address": IP["leaf12"]}])])
        self.assertEqual(self.port_posts()[:2], [[("pv-isolated", SN["leaf11"], "", "Ethernet1/41", True)],
                                                 [("pv-isolated", SN["leaf11"], "", "", False)]])
        self.assertEqual(self.ndfc.attached("pv-isolated"), [SN["leaf12"]])

    def test_ports_deleted_and_overridden_family(self):
        """deleted and overridden: every port detach precedes the switch detaches; the primary is deleted last."""
        for state in ("deleted", "overridden"):
            with self.subTest(state=state):
                self.ndfc.networks, self.ndfc.rows = {}, {}
                self.seed_family()
                self.ndfc.attach("pv-isolated", "leaf13", ports="Port-channel543")
                self.ndfc.attach("pv-isolated", "leaf14", ports="Port-channel544")
                self.ndfc.attach("pv-community", "leaf11", ports="Port-channel541")
                config = ([{"net_name": "pv-isolated"}, {"net_name": "pv-community"}, {"net_name": "pv-primary"}] if state == "deleted"
                          else [self.regular_l2()])
                self.run_module(state, config)
                self.assertEqual(sorted(self.port_posts()[0]), sorted([("pv-isolated", SN["leaf13"], "", "Port-channel543", True),
                                                                       ("pv-isolated", SN["leaf14"], "", "Port-channel544", True),
                                                                       ("pv-community", SN["leaf11"], "", "Port-channel541", True)]))
                self.assertTrue(all(item[2] == "" for item in self.port_items(deployment=False)))
                deletes = [path.rsplit("/", 1)[-1] for method, path, body in self.ndfc.writes() if method == "DELETE"]
                self.assertEqual(deletes[-1], "pv-primary")
                self.assertEqual(self.ndfc.networks.keys() & {"pv-isolated", "pv-community", "pv-primary"}, set())

    def test_ports_kept_family_row_keeps_its_ports(self):
        """The family rule: a secondary row kept on a switch where its primary stays is not detached, and its ports are not
        reconciled."""
        self.seed_family(primary_on=("leaf11",))
        self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41")
        self.ndfc.attach("pv-isolated", "leaf12")
        config = [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf12"]}]),
                  self.existing_net("pv-primary", 2431, [{"ip_address": IP["leaf11"]}, {"ip_address": IP["leaf12"]}])]
        result = self.run_module("replaced", config)
        self.assertFalse(result["changed"], result)
        self.assertEqual(self.ports_on("pv-isolated", "leaf11"), "Ethernet1/41")

    def test_ports_item_refused_inside_http_200(self):
        """A port in the wrong PVLAN mode: the per-item refusal fails the task, no rollback, the write is reported."""
        self.seed_family()
        self.ndfc.inject.append(("POST", ATTACH, ok("POST", ATTACH, {"pv-isolated-[PVL0000011/leaf-11]": self.fixtures["port_refusal_text"]})))
        result = self.run_module("merged", [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/44"]}])], failed=True)
        self.assertIn("Invalid Interfaces", json.dumps(result["msg"]["FAILED_ITEMS"]))
        self.assertIn("NOT ATTEMPTED", result["msg"]["ROLLBACK_RESULT"])
        self.assertEqual([request for request in self.ndfc.writes() if request[0] == "DELETE"], [])

    def test_ports_port_detach_refused_stops_before_switch_detach(self):
        """The switch detach depends on the port detach: a refused port detach fails the run before the switch detach
        is sent, and the acknowledged write lists the refused item."""
        self.seed_family()
        self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41")
        self.ndfc.attach("pv-isolated", "leaf12")
        self.ndfc.inject.append(("POST", ATTACH, ok("POST", ATTACH, {"pv-isolated-[PVL0000011/leaf-11]": "Invalid Interfaces in leaf-11"})))
        result = self.run_module("replaced", [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf12"]}]),
                                              self.existing_net("pv-primary", 2431, [{"ip_address": IP["leaf12"]}])], failed=True)
        self.assertEqual(self.port_posts(), [[("pv-isolated", SN["leaf11"], "", "Ethernet1/41", True)]])
        self.assertEqual([request for request in self.ndfc.writes() if "deploy" in request[1]], [])
        outcomes = [write["outcome"] for write in result["acknowledged_writes"]]
        self.assertEqual(outcomes, ["items_refused"])
        self.assertEqual(self.ports_on("pv-isolated", "leaf11"), "Ethernet1/41")

    def test_ports_split_does_not_change_the_planned_rows(self):
        """The port detach and the portless switch detach are copies; the planned rows keep their ports."""
        self.seed_family()
        self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41")
        self.ndfc.attach("pv-isolated", "leaf12")
        seen = []
        push = dcnm_network.DcnmNetwork.pvlan_push_attachments

        def spy(module_self, payload, detach_step):
            before = [(item["serialNumber"], item.get("switchPorts"), item.get("deployment")) for entry in payload for item in entry["lanAttachList"]]
            push(module_self, payload, detach_step)
            after = [(item["serialNumber"], item.get("switchPorts"), item.get("deployment")) for entry in payload for item in entry["lanAttachList"]]
            seen.append((before, after))

        with patch.object(dcnm_network.DcnmNetwork, "pvlan_push_attachments", autospec=True, side_effect=spy):
            self.run_module("replaced", [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf12"]}]),
                                         self.existing_net("pv-primary", 2431, [{"ip_address": IP["leaf12"]}])])
        self.assertTrue(any((SN["leaf11"], "Ethernet1/41", False) in before for before, after in seen))
        for before, after in seen:
            self.assertEqual(before, after)

    def test_ports_check_mode_save_and_deploy(self):
        self.seed_family()
        entry = self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/41"]}])
        self.assertTrue(self.run_module("merged", [entry], check_mode=True)["changed"])
        self.assert_no_writes()
        self.run_module("merged", [dict(entry, deploy=False)])
        self.assertEqual([r for r in self.ndfc.writes() if "deploy" in r[1]], [])
        self.run_module("merged", [dict(entry, deploy=True)])
        self.assertEqual([method for method, path, body in self.ndfc.writes()], ["POST"])
        self.assertIn("config-deploy", self.ndfc.writes()[0][1])
        self.assertFalse(self.run_module("merged", [dict(entry, deploy=True)])["changed"])

    def test_ports_vpc_one_peer_change_and_deploy_scope(self):
        """One peer's port-channel changes: the other peer is re-sent without ports and keeps its port, and both peers are
        deployed (config-deploy of both serials, or a network deploy naming the network on both)."""
        scopes = {}
        for deploy_mode in (None, "resource"):
            self.ndfc.networks, self.ndfc.rows = {}, {}
            self.seed_family()
            self.ndfc.attach("pv-isolated", "leaf13", ports="Port-channel543")
            self.ndfc.attach("pv-isolated", "leaf14", ports="Port-channel544")
            self.run_module("replaced", [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf13"], "ports": ["Port-channel543"]},
                                                                                 {"ip_address": IP["leaf14"], "ports": ["Port-channel545"]}])],
                            deploy_mode=deploy_mode)
            self.assertEqual(sorted(i[1:4] for i in self.port_items()), sorted([(SN["leaf13"], "", ""), (SN["leaf14"], "Port-channel545", "Port-channel544")]))
            self.assertEqual(self.ports_on("pv-isolated", "leaf13"), "Port-channel543")
            scopes[deploy_mode or "switch"] = [(path, body) for method, path, body in self.ndfc.writes() if "deploy" in path]
        self.assertEqual(len(scopes["switch"]), 1)
        self.assertEqual(set(scopes["switch"][0][0].split("/config-deploy/")[1].split("?")[0].split(",")), {SN["leaf13"], SN["leaf14"]})
        self.assertEqual(len(scopes["resource"]), 1)
        self.assertEqual(set(scopes["resource"][0][1]), {SN["leaf13"], SN["leaf14"]})

    def test_ports_overlay_policies_are_not_freeform(self):
        """The OVERLAY policy an attachment creates on its port (templateName NA) is not read as attachment freeform."""
        self.seed_family()
        self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41")
        self.ndfc.policies[SN["leaf11"]] = [dict(policy, serialNumber=SN["leaf11"]) for policy in self.fixtures["port_policies"]["policies"]]
        config = [self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/41"]}])]
        for state in ("merged", "replaced"):
            self.assertFalse(self.run_module(state, config)["changed"], state)

    def test_ports_identity_is_per_switch(self):
        """The same port name on two switches is two attachments; a mixed request keeps the regular item."""
        self.seed_family()
        self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41")
        self.ndfc.attach("pv-isolated", "leaf12", ports="Ethernet1/41")
        attach = [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/41"]}, {"ip_address": IP["leaf12"]}]
        self.run_module("replaced", [self.existing_net("pv-isolated", 2432, attach)])
        self.assertEqual(self.port_items(), [("pv-isolated", SN["leaf12"], "", "Ethernet1/41", True)])
        self.assertEqual(self.ports_on("pv-isolated", "leaf11"), "Ethernet1/41")

        self.run_module("merged", [self.regular_l2([{"ip_address": IP["leaf12"], "ports": ["Ethernet1/10"]}]),
                                   self.existing_net("pv-isolated", 2432, [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/42"]}])])
        self.assertIn(("reg-l2", SN["leaf12"], "Ethernet1/10", "", True), self.port_items())
        self.assertIn(("pv-isolated", SN["leaf11"], "Ethernet1/42", "", True), self.port_items())

    # ----- changed after a failure -------------------------------------------
    #
    # A failed run keeps the writes the controller applied before the failure, so the failure reports changed from
    # the writes of the whole run, not from the last response. A write the module judged failed may or may not have
    # changed anything: it does not set changed.

    def assert_failed_changed(self, result, expected):
        self.assertTrue(result["failed"])
        self.assertIn("changed", result, "a failed PVLAN run reports changed")
        self.assertIs(result["changed"], expected, result.get("acknowledged_writes"))

    def test_failure_changed_true_after_earlier_write(self):
        """A write acknowledged before the failure sets changed: create, update, attach, detach and delete, in
        PVLAN-only and mixed requests, and a partly accepted attachment POST."""

        # primary created, secondary refused (PVLAN only)
        def primary_then_secondary():
            self.ndfc.fail_network[("POST", "pv-isolated")] = bad("POST", NETS, "simulated controller error")
            return "merged", self.family(), {}

        # regular bulk create and primary created, secondary refused (mixed)
        def mixed_create():
            self.ndfc.fail_network[("POST", "pv-isolated")] = bad("POST", NETS, "simulated controller error")
            regular = {"net_name": "reg-l2", "net_id": 30101, "vlan_id": 2101, "is_l2only": True, "attach": [{"ip_address": IP["leaf12"]}]}
            return "merged", [regular] + self.family(isolated_attach=("leaf11",)), {}

        # regular bulk create accepted, the first PVLAN write refused: the bulk write is the only earlier write
        def regular_then_first_pvlan_refused():
            self.ndfc.fail_network[("POST", "pv-primary")] = bad("POST", NETS, "simulated controller error")
            regular = {"net_name": "reg-l2", "net_id": 30101, "vlan_id": 2101, "is_l2only": True}
            return "merged", [regular] + self.family(), {}

        # regular bulk update, then a PVLAN update refused
        def update_then_refusal():
            self.seed_family()
            self.ndfc.seed("regular", "reg-a", 30100, 2100)
            self.ndfc.inject.append(("PUT", NETS + "/pv-isolated", bad("PUT", NETS + "/pv-isolated", "simulated controller error")))
            config = [{"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "vlan_name": "ISO_NEW"},
                      {"net_name": "reg-a", "is_l2only": True, "vlan_name": "REG_NEW"}]
            return "merged", config, {}

        # attachment POST: one item applied, one refused inside HTTP 200, and nothing written before it
        def partly_accepted_attachment():
            self.seed_family()
            self.ndfc.refuse[("pv-community", SN["leaf12"])] = "Invalid Interfaces (simulated)"
            return "merged", self.family(isolated_attach=("leaf11",), community_attach=("leaf12",))[:2], {}

        # detach acknowledged, then the deploy is refused
        def detach_then_deploy_refused():
            self.seed_family(isolated_on=("leaf11",), community_on=("leaf12",))
            self.ndfc.inject.append(("POST", "?forceShowRun=false", bad("POST", self.CONFIG_DEPLOY, "simulated deploy error")))
            return "deleted", [{"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}], {}

        # regular bulk delete, then a PVLAN delete refused (mixed)
        def mixed_delete():
            self.ndfc.seed("regular", "reg-old", 30101, 2101)
            self.seed_family()
            self.ndfc.fail_network[("DELETE", "pv-community")] = bad("DELETE", NETS + "/pv-community", "simulated controller error")
            return "deleted", [{"net_name": "reg-old"}, {"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}], {}

        # a PVLAN delete accepted, then the next one refused
        def delete_then_refusal():
            self.seed_family()
            self.ndfc.fail_network[("DELETE", "pv-community")] = bad("DELETE", NETS + "/pv-community", "simulated controller error")
            return "deleted", [{"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}], {}

        for build in (primary_then_secondary, mixed_create, regular_then_first_pvlan_refused, update_then_refusal, partly_accepted_attachment,
                      detach_then_deploy_refused, mixed_delete, delete_then_refusal):
            with self.subTest(case=build.__name__):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.ndfc.inject.clear()
                self.ndfc.fail_network.clear()
                self.ndfc.refuse.clear()
                state, config, kwargs = build()
                result = self.run_module(state, config, failed=True, **kwargs)
                self.assertIn("acknowledged writes remain applied", result["msg"]["ROLLBACK_RESULT"])
                self.assertTrue(result["acknowledged_writes"], "the run wrote before it failed")
                self.assert_failed_changed(result, True)
                if build is partly_accepted_attachment:
                    self.assertEqual(self.ndfc.attached("pv-isolated"), [SN["leaf11"]], "the accepted item was applied")
                    self.assertEqual(self.ndfc.attached("pv-community"), [], "the refused item was not")
                self.assertIn("pvlan_state", result)
                self.assertIn("response", result)

    def test_failure_changed_not_reset_by_a_later_response(self):
        """A later response sets the per-response result['changed'] again: an accepted deploy that found nothing
        pending reads False after the detach before it was applied. The failure reports the whole run. The row
        stays PENDING, so the run exits in the wait before deletion and no DELETE is sent."""
        self.seed_family(isolated_on=("leaf11",))
        nothing = {"RETURN_CODE": 200, "METHOD": "POST", "MESSAGE": "OK", "REQUEST_PATH": self.CONFIG_DEPLOY,
                   "DATA": {"status": "No switches PENDING for deployment"}}
        self.ndfc.inject.append(("POST", "?forceShowRun=false", nothing))
        result = self.run_module("deleted", [{"net_name": "pv-isolated"}], failed=True)
        self.assertIn("did not reach a state ready for deletion", str(result["msg"]))
        self.assertNotIn("DELETE", [method for method, _path, _data in self.ndfc.requests])
        self.assertEqual([write["outcome"] for write in result["acknowledged_writes"]], ["acknowledged", "acknowledged"])
        self.assertEqual([write["method"] for write in result["acknowledged_writes"]], ["POST", "POST"])
        self.assertEqual(self.ndfc.rows[("pv-isolated", SN["leaf11"])]["state"], "PENDING", "the detach was applied")
        self.assert_failed_changed(result, True)

    def answer_bulk_delete_with_500(self, refused):
        """Answer the regular bulk delete as the controller does for a partial deletion: HTTP 500 with successList
        and failureList. The listed successes are deleted; the names in refused stay."""
        send = self.ndfc.send

        def traced(module, method, path, data=None):
            if method == "DELETE" and "/bulk-delete/networks?network-names=" in path:
                self.ndfc.requests.append((method, path, None))
                names = path.split("=", 1)[1].split(",")
                done = [name for name in names if name not in refused]
                for name in done:
                    self.ndfc.delete(method, path, name)
                return {"RETURN_CODE": 500, "METHOD": method, "MESSAGE": "Internal Server Error", "REQUEST_PATH": path,
                        "DATA": {"successList": done,
                                 "failureList": [{"name": name, "message": "simulated refusal"} for name in names if name in refused]}}
            return send(module, method, path, data)

        self.patches[0].stop()
        self.patches[0] = patch("ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_send", side_effect=traced)
        self.patches[0].start()

    def test_failure_changed_true_after_partial_bulk_delete(self):
        """A regular bulk delete answered with HTTP 500 and a nonempty successList deleted a network, as
        bulk_delete_networks_with_retry() records. The mixed request then fails and changed stays true, although
        acknowledged_writes lists 2xx responses only and the last attempt lists no success."""
        self.ndfc.seed("regular", "reg-a", 30101, 2101)
        self.ndfc.seed("regular", "reg-b", 30102, 2102)
        self.seed_family()
        self.answer_bulk_delete_with_500({"reg-b"})
        config = [{"net_name": "reg-a"}, {"net_name": "reg-b"}, {"net_name": "pv-primary"}, {"net_name": "pv-isolated"},
                  {"net_name": "pv-community"}]
        result = self.run_module("deleted", config, failed=True)
        self.assertNotIn("reg-a", self.ndfc.networks, "the bulk delete removed reg-a")
        self.assertEqual([m for m, _p, _d in self.ndfc.requests if m != "GET"], ["DELETE"] * 3, "only the three bulk attempts")
        self.assertEqual(result["acknowledged_writes"], [])
        self.assert_failed_changed(result, True)

    def test_failure_changed_false_when_bulk_delete_lists_no_success(self):
        """The same 500 with an empty successList on every attempt deleted nothing: changed stays false."""
        self.ndfc.seed("regular", "reg-a", 30101, 2101)
        self.seed_family()
        self.answer_bulk_delete_with_500({"reg-a"})
        config = [{"net_name": "reg-a"}, {"net_name": "pv-primary"}, {"net_name": "pv-isolated"}, {"net_name": "pv-community"}]
        result = self.run_module("deleted", config, failed=True)
        self.assertIn("reg-a", self.ndfc.networks)
        self.assert_failed_changed(result, False)

    def test_failure_changed_false_without_an_applied_write(self):
        """No write was applied: the first write is refused, every item of an HTTP 200 attachment POST is refused,
        or a read fails before any write."""

        def first_write_refused():
            self.ndfc.fail_network[("POST", "pv-primary")] = bad("POST", NETS, "simulated controller error")
            return "merged", self.family()

        def all_items_refused():
            self.seed_family()
            self.ndfc.refuse[("pv-community", SN["leaf12"])] = "Invalid Interfaces (simulated)"
            return "merged", [{"net_name": "pv-community", "is_l2only": True, "attach": [{"ip_address": IP["leaf12"]}]}]

        def read_fails_before_any_write():
            self.ndfc.inject.append(("GET", self.VLAN_POOL, bad("GET", self.VLAN_POOL, "simulated vlan pool error")))
            return "merged", [{"net_name": "reg-new", "net_id": 30150, "is_l2only": True}] + self.family()[2:]

        for build in (first_write_refused, all_items_refused, read_fails_before_any_write):
            with self.subTest(case=build.__name__):
                self.ndfc.networks.clear()
                self.ndfc.rows.clear()
                self.ndfc.inject.clear()
                self.ndfc.fail_network.clear()
                self.ndfc.refuse.clear()
                state, config = build()
                result = self.run_module(state, config, failed=True)
                self.assert_failed_changed(result, False)
                self.assertEqual([write for write in result["acknowledged_writes"] if write["outcome"] == "acknowledged"], [])

    def test_failure_changed_false_after_the_bulk_capability_probe(self):
        """The empty bulk-capability probe is a POST that changes nothing and is not a response of the run: a run
        that sent it and then had its first write refused reports changed false."""
        probes = []

        def send(module, method, path, data=None, *args, **kwargs):
            if method == "POST" and path.endswith("/v2/bulk-update/networks"):
                probes.append((method, path, data))
                return {"RETURN_CODE": 405, "METHOD": method, "MESSAGE": "Method Not Allowed", "REQUEST_PATH": path, "DATA": {}}
            return self.ndfc.send(module, method, path, data)

        self.ndfc.fail_network[("POST", "pv-primary")] = bad("POST", NETS, "simulated controller error")
        with patch("ansible_collections.cisco.dcnm.plugins.modules.dcnm_network.dcnm_get_bulk_api_support",
                   side_effect=dcnm_get_bulk_api_support), \
                patch("ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm.dcnm_send", side_effect=send):
            result = self.run_module("merged", self.family(), failed=True)
        self.assertEqual(len(probes), 1, "the capability probe was sent")
        self.assertEqual(result["acknowledged_writes"], [], "the probe is not a response of the run")
        self.assert_failed_changed(result, False)

    def test_failure_changed_false_for_a_write_judged_failed(self):
        """A response the module judged failed is not counted: HTTP 200 with an ERROR key or an error text in a
        string DATA may or may not have been applied. It stays listed in acknowledged_writes as failed, which tells
        it apart from a refusal with a non-2xx status that never appears there."""
        error = {"RETURN_CODE": 200, "METHOD": "POST", "MESSAGE": "OK", "REQUEST_PATH": NETS, "DATA": {}, "ERROR": "simulated body-level error"}
        self.ndfc.inject.append(("POST", NETS, error))
        result = self.run_module("merged", self.family(), failed=True)
        self.assertEqual([(write["method"], write["outcome"]) for write in result["acknowledged_writes"]], [("POST", "failed")])
        self.assert_failed_changed(result, False)

        self.ndfc.rows.clear()
        self.seed_family(isolated_on=("leaf11",))
        text = {"RETURN_CODE": 200, "METHOD": "POST", "MESSAGE": "OK", "REQUEST_PATH": ATTACH, "DATA": "Invalid interfaces supplied"}
        self.ndfc.inject.append(("POST", ATTACH, text))
        result = self.run_module("merged", [{"net_name": "pv-community", "is_l2only": True, "attach": [{"ip_address": IP["leaf12"]}]}], failed=True)
        self.assertEqual([(write["method"], write["outcome"]) for write in result["acknowledged_writes"]], [("POST", "failed")])
        self.assert_failed_changed(result, False)

    def test_failure_changed_survives_a_state_read_failure(self):
        """A failed state read leaves pvlan_state unknown; it does not erase the earlier write or the original error."""
        self.ndfc.fail_network[("POST", "pv-isolated")] = bad("POST", NETS, "simulated controller error")
        # the first list read belongs to the request itself, the next one to the state read after the failure
        self.ndfc.inject.append(("GET", NETS, bad("GET", NETS, "simulated read error"), 1))
        result = self.run_module("merged", self.family(), failed=True)
        self.assertIn("RETURN_CODE", result["pvlan_state"]["read_error"])
        self.assertEqual(result["msg"]["DATA"], {"message": "simulated controller error"})
        self.assertTrue(result["acknowledged_writes"])
        self.assert_failed_changed(result, True)

    # vPC pairs in the port detach step

    FAMILY_DELETE = [{"net_name": "pv-isolated"}, {"net_name": "pv-community"}, {"net_name": "pv-primary"}]
    MEASURED_SWITCH = {"PVL0000013": "leaf13", "PVL0000014": "leaf14"}

    def seed_measured_pair(self):
        """The measured pre-delete family on one vPC pair (fixture vpc_pair_measured.pre_rows): the three networks attached to
        both peers, the primary with one port on leaf-13 only."""
        self.seed_family()
        for row in self.fixtures["vpc_pair_measured"]["pre_rows"]:
            self.ndfc.attach(row["networkName"], self.MEASURED_SWITCH[row["switchSerialNo"]], state=row["lanAttachState"],
                             ports=row["portNames"], instance=row["instanceValues"])

    def attach_writes(self):
        return [(method, path.rsplit("/", 1)[-1] if method == "DELETE" else path) for method, path, body in self.ndfc.writes()]

    def test_vpc_pair_double_matches_the_measured_answers(self):
        """The double refuses the measured one-peer port detach with the measured text and accepts the measured attach that
        names both peers."""
        self.seed_measured_pair()
        measured = self.fixtures["vpc_pair_measured"]
        answer = self.ndfc.attachments("POST", ATTACH, copy.deepcopy(measured["lone_port_detach"]))["DATA"]
        self.assertEqual(answer, {"pv-primary-[PVL0000013/leaf-13]": measured["lone_port_detach_answer"].format(peer=SN["leaf14"])})
        self.assertEqual(self.ports_on("pv-primary", "leaf13"), "Ethernet1/44")
        self.ndfc.rows[("pv-primary", SN["leaf13"])]["ports"] = ""
        answer = self.ndfc.attachments("POST", ATTACH, copy.deepcopy(measured["pair_attach"]))["DATA"]
        self.assertEqual(set(answer.values()), {"SUCCESS"})

    def test_vpc_port_detach_names_both_peers(self):
        """Measured case: a delete of a family on a vPC pair whose primary holds a port on one peer only. The port detach
        names both peers; the other peer is re-sent attached without ports. Then the switch detaches, one deploy and the
        deletes follow in the same order as before."""
        measured = self.fixtures["vpc_pair_measured"]["lone_port_detach"][0]["lanAttachList"][0]
        for deploy_mode in ("resource", None):
            with self.subTest(deploy_mode=deploy_mode):
                self.ndfc.networks, self.ndfc.rows = {}, {}
                self.seed_measured_pair()
                result = self.run_module("deleted", self.FAMILY_DELETE, deploy_mode=deploy_mode)
                self.assertTrue(result["changed"])
                posts = self.port_posts()
                self.assertEqual(sorted(posts[0]), sorted([("pv-primary", SN["leaf13"], "", "Ethernet1/44", True),
                                                           ("pv-primary", SN["leaf14"], "", "", True)]))
                sent = {item["serialNumber"]: item for item in self.bodies("POST", ATTACH)[0][0]["lanAttachList"]}
                self.assertEqual({key: sent[SN["leaf13"]].get(key) for key in measured}, measured)
                # The re-sent peer has the fields of the peer row of the measured attach that named both peers.
                peer = next(item for item in self.fixtures["vpc_pair_measured"]["pair_attach"][0]["lanAttachList"] if item["serialNumber"] == SN["leaf14"])
                self.assertEqual({key: sent[SN["leaf14"]].get(key) for key in peer}, peer)
                self.assertTrue(all(item[4] is False and item[2] == "" for post in posts[1:] for item in post))
                self.assertEqual(sorted(item[:2] for post in posts[1:] for item in post),
                                 sorted((name, SN[leaf]) for name in ("pv-isolated", "pv-community", "pv-primary") for leaf in ("leaf13", "leaf14")))
                writes = self.attach_writes()
                self.assertEqual([w[0] for w in writes].count("DELETE"), 3)
                self.assertEqual(len([w for w in writes if "deploy" in w[1]]), 1)
                self.assertEqual(self.ndfc.networks.keys() & {"pv-isolated", "pv-community", "pv-primary"}, set())
                self.assertEqual(self.ndfc.lone_vpc_detaches, [])
                self.assertFalse(self.run_module("deleted", self.FAMILY_DELETE, deploy_mode=deploy_mode)["changed"])
                self.assert_no_writes()

    def test_vpc_port_detach_check_mode_writes_nothing(self):
        self.seed_measured_pair()
        self.assertTrue(self.run_module("deleted", self.FAMILY_DELETE, check_mode=True)["changed"])
        self.assert_no_writes()
        self.assertEqual(self.ports_on("pv-primary", "leaf13"), "Ethernet1/44")

    def test_vpc_port_detach_when_both_or_neither_peer_has_ports(self):
        """Both peers with ports (different names): each peer sends its own port detach and no other row. Neither peer
        with ports: no port detach step."""
        self.seed_measured_pair()
        self.ndfc.rows[("pv-primary", SN["leaf14"])]["ports"] = "Ethernet1/45"
        self.run_module("deleted", self.FAMILY_DELETE)
        self.assertEqual(sorted(self.port_posts()[0]), sorted([("pv-primary", SN["leaf13"], "", "Ethernet1/44", True),
                                                               ("pv-primary", SN["leaf14"], "", "Ethernet1/45", True)]))
        self.ndfc.networks, self.ndfc.rows = {}, {}
        self.seed_measured_pair()
        self.ndfc.rows[("pv-primary", SN["leaf13"])]["ports"] = ""
        self.run_module("deleted", self.FAMILY_DELETE)
        self.assertEqual(self.port_items(deployment=True), [])
        self.assertEqual(self.ndfc.networks.keys() & {"pv-isolated", "pv-community", "pv-primary"}, set())

    def test_vpc_port_detach_keeps_the_ports_of_a_peer_that_stays(self):
        """replaced: the primary leaves leaf-13 (with its port) and stays on leaf-14, where a community network outside the
        request keeps it. The port detach re-sends leaf-14 without ports; its own port and attachment stay."""
        self.seed_family()
        self.ndfc.attach("pv-primary", "leaf13", ports="Ethernet1/44")
        self.ndfc.attach("pv-primary", "leaf14", ports="Ethernet1/45")
        self.ndfc.attach("pv-community", "leaf14")
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        config = [{"net_name": "pv-primary", "is_l2only": True, "vlan_id": 2431, "multicast_group_address": mcast, "attach": []}]
        self.run_module("replaced", config)
        self.assertEqual(sorted(self.port_posts()[0]), sorted([("pv-primary", SN["leaf13"], "", "Ethernet1/44", True),
                                                               ("pv-primary", SN["leaf14"], "", "", True)]))
        self.assertEqual(self.ports_on("pv-primary", "leaf14"), "Ethernet1/45")
        self.assertEqual(self.ndfc.attached("pv-primary"), [SN["leaf14"]])
        # The switch detach of leaf-13 alone is applied by the double; that answer is not measured.
        self.assertEqual(self.ndfc.lone_vpc_detaches, [("pv-primary", SN["leaf13"])])

    def test_vpc_peer_that_is_not_attached_is_not_added(self):
        """A vPC switch whose peer is not attached to the network: no peer row is invented. The controller's refusal is
        reported and nothing after it is sent."""
        self.seed_family()
        self.ndfc.attach("pv-primary", "leaf13", ports="Ethernet1/44")
        result = self.run_module("deleted", self.FAMILY_DELETE, failed=True)
        self.assertEqual(self.port_posts(), [[("pv-primary", SN["leaf13"], "", "Ethernet1/44", True)]])
        self.assertIn("VPC details not found for Peer Serial no: " + SN["leaf14"], json.dumps(result["msg"]["FAILED_ITEMS"]))
        self.assertEqual([w for w in self.attach_writes() if w[0] == "DELETE" or "deploy" in w[1]], [])

    def test_vpc_peer_identity_problems_refuse_before_any_write(self):
        """A vPC switch without a peer serial in the inventory, or an attachment that names another peer, is refused before
        any write."""
        for case in ("no inventory peer", "other peer"):
            with self.subTest(case=case):
                self.ndfc.networks, self.ndfc.rows = {}, {}
                self.ndfc.inventory = copy.deepcopy(self.fixtures["inventory_pvlan"])
                self.seed_measured_pair()
                entry = self.ndfc.attach_entry
                if case == "no inventory peer":
                    self.ndfc.inventory[IP["leaf13"]]["peerSerialNumber"] = None
                else:
                    def attach_entry(name, entry=entry):
                        out = entry(name)
                        for row in out["lanAttachList"]:
                            if row["switchSerialNo"] == SN["leaf13"]:
                                row["peerSerialNo"] = "PVL0000099"
                        return out
                    self.ndfc.attach_entry = attach_entry
                result = self.run_module("deleted", self.FAMILY_DELETE, failed=True)
                self.assertIn("PVLAN port detach refused before any write", result["msg"])
                self.assert_no_writes()
                self.ndfc.attach_entry = entry

    def test_vpc_two_pairs_and_a_standalone_switch(self):
        """Two vPC pairs and a standalone switch in one delete: each pair's port detach names its own peer, the standalone
        switch is sent alone."""
        extra = {"leaf15": ("PVL0000015", "192.0.2.15", "PVL0000016"), "leaf16": ("PVL0000016", "192.0.2.16", "PVL0000015")}
        with patch.dict(SN, {k: v[0] for k, v in extra.items()}), patch.dict(IP, {k: v[1] for k, v in extra.items()}):
            for switch, (serial, ip, peer) in extra.items():
                self.ndfc.inventory[ip] = dict(self.ndfc.inventory[IP["leaf13"]], ipAddress=ip, logicalName=switch.replace("leaf", "leaf-"),
                                               serialNumber=serial, peerSerialNumber=peer)
            self.seed_measured_pair()
            self.ndfc.attach("pv-primary", "leaf15", ports="Ethernet1/44")
            self.ndfc.attach("pv-primary", "leaf16")
            self.ndfc.attach("pv-community", "leaf11", ports="Ethernet1/41")
            self.run_module("deleted", self.FAMILY_DELETE)
            self.assertEqual(sorted(self.port_posts()[0]), sorted([
                ("pv-primary", SN["leaf13"], "", "Ethernet1/44", True), ("pv-primary", SN["leaf14"], "", "", True),
                ("pv-primary", SN["leaf15"], "", "Ethernet1/44", True), ("pv-primary", SN["leaf16"], "", "", True),
                ("pv-community", SN["leaf11"], "", "Ethernet1/41", True)]))
            self.assertEqual(self.ndfc.networks.keys() & {"pv-isolated", "pv-community", "pv-primary"}, set())

    def test_vpc_port_detach_of_a_secondary_and_the_implicit_primary(self):
        """A secondary with a port on one peer: the peer is named in the port detach. The implicit primary is removed with
        its last secondary, or stays under another secondary, as before."""
        for keep in (False, True):
            with self.subTest(keep=keep):
                self.ndfc.networks, self.ndfc.rows = {}, {}
                self.seed_family()
                self.ndfc.attach("pv-isolated", "leaf13", ports="Port-channel543")
                self.ndfc.attach("pv-isolated", "leaf14")
                if keep:
                    self.ndfc.attach("pv-community", "leaf13")
                    self.ndfc.attach("pv-community", "leaf14")
                self.run_module("deleted", [{"net_name": "pv-isolated"}])
                self.assertEqual(sorted(self.port_posts()[0]), sorted([("pv-isolated", SN["leaf13"], "", "Port-channel543", True),
                                                                       ("pv-isolated", SN["leaf14"], "", "", True)]))
                self.assertNotIn("pv-isolated", self.ndfc.networks)
                self.assertEqual(self.ndfc.attached("pv-primary"), [SN["leaf13"], SN["leaf14"]] if keep else [])

    def test_vpc_port_detach_with_a_regular_network(self):
        """A regular network on the same pair is detached as before: its rows keep their ports in one switch detach POST,
        without a port detach step or a re-sent peer."""
        self.seed_measured_pair()
        self.seed_regular_l2({"leaf13": "Ethernet1/10", "leaf14": ""})
        self.run_module("deleted", self.FAMILY_DELETE + [{"net_name": "reg-l2"}])
        self.assertEqual(sorted(self.port_posts()[0]), sorted([("pv-primary", SN["leaf13"], "", "Ethernet1/44", True),
                                                               ("pv-primary", SN["leaf14"], "", "", True)]))
        regular = [item for post in self.port_posts() for item in post if item[0] == "reg-l2"]
        self.assertEqual(sorted(regular), sorted([("reg-l2", SN["leaf13"], "Ethernet1/10", "", False), ("reg-l2", SN["leaf14"], "", "", False)]))
        self.assertEqual(len([post for post in self.port_posts() if any(item[0] == "reg-l2" for item in post)]), 1)

    def test_vpc_overridden_removes_the_measured_family(self):
        self.seed_measured_pair()
        self.run_module("overridden", [self.regular_l2()])
        self.assertEqual(sorted(self.port_posts()[0]), sorted([("pv-primary", SN["leaf13"], "", "Ethernet1/44", True),
                                                               ("pv-primary", SN["leaf14"], "", "", True)]))
        self.assertEqual(self.ndfc.networks.keys() & {"pv-isolated", "pv-community", "pv-primary"}, set())

    def test_vpc_port_detach_item_refused_inside_http_200(self):
        """A refused item of the port detach step (the port's switch or the re-sent peer): the run stops before the switch
        detaches, the deploy and the deletes, and reports exactly the refused item."""
        for refused in ("leaf13", "leaf14"):
            with self.subTest(refused=refused):
                self.ndfc.networks, self.ndfc.rows = {}, {}
                self.seed_measured_pair()
                self.ndfc.refuse = {("pv-primary", SN[refused]): "Attach Response : Failed : simulated"}
                result = self.run_module("deleted", self.FAMILY_DELETE, failed=True)
                self.assertEqual(len(self.port_posts()), 1)
                key = "pv-primary-[{0}/{1}]".format(SN[refused], refused.replace("leaf", "leaf-"))
                self.assertEqual(result["msg"]["FAILED_ITEMS"], [{key: "Attach Response : Failed : simulated"}])
                self.assertEqual([w for w in self.attach_writes() if w[0] == "DELETE" or "deploy" in w[1]], [])
                self.assertEqual([write["outcome"] for write in result["acknowledged_writes"]], ["items_refused"])
                self.assertEqual(self.ports_on("pv-primary", "leaf13"), "Ethernet1/44" if refused == "leaf13" else "")
                self.ndfc.refuse = {}


def dcnm_network_exit():
    from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson

    return AnsibleExitJson
