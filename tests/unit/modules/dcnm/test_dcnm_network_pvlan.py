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
    - a PUT replaces the stored template config.

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

    def attach(self, name, switch, explicit=True, state="DEPLOYED", ports=""):
        serial = SN[switch]
        self.rows[(name, serial)] = {"attached": True, "state": state, "ports": ports, "explicit": explicit}
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
                "instanceValues": '{"sviEnabled":"true"}' if row else None,
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

    def attachments(self, method, path, body):
        data = {}
        for entry in body:
            name = entry["networkName"]
            for item in entry["lanAttachList"]:
                serial = item["serialNumber"]
                key = "{0}-[{1}/{2}]".format(name, serial, self.switch_name(serial))
                if name not in self.networks:
                    data[key] = "Invalid network " + name
                elif (name, serial) in self.refuse:
                    data[key] = self.refuse[(name, serial)]
                elif item.get("deployment"):
                    data[key] = self.attach_item(name, serial, item)
                else:
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

    def test_named_ports_rejected(self):
        """Port attachments on a PVLAN network are rejected."""
        config = self.family()
        config[0]["attach"] = [{"ip_address": IP["leaf11"], "ports": ["Ethernet1/41"]}]
        result = self.run_module("merged", config, failed=True)
        self.assertIn("attach switches only", result["msg"])
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

    def test_existing_named_ports_boundary(self):
        """Existing named ports on a PVLAN network block replaced/overridden/deleted; merged and query pass."""
        self.seed_family()
        self.ndfc.attach("pv-isolated", "leaf11", ports="Ethernet1/41")
        mcast = json.loads(self.ndfc.networks["pv-primary"]["networkTemplateConfig"])["mcastGroup"]
        isolated = {"net_name": "pv-isolated", "vlan_id": 2432, "is_l2only": True, "multicast_group_address": mcast, "attach": [{"ip_address": IP["leaf11"]}]}
        for state, config in (("replaced", [isolated]), ("overridden", [{"net_name": "reg-z", "net_id": 30199, "vlan_id": 2199, "is_l2only": True}]),
                              ("deleted", [{"net_name": "pv-isolated"}])):
            with self.subTest(state=state):
                result = self.run_module(state, config, failed=True)
                self.assertIn("Ethernet1/41", result["msg"])
                self.assert_no_writes()
        self.assertFalse(self.run_module("merged", [isolated])["changed"])
        self.ndfc.seed("regular", "reg-routed", 30100, 2100, vrf="VRF_A", isLayer2Only="false")
        query = self.run_module("query", [{"net_name": "pv-isolated"}])
        self.assertIn("Ethernet1/41", json.dumps(query["response"]))

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


def dcnm_network_exit():
    from ansible_collections.ansible.netcommon.tests.unit.modules.utils import AnsibleExitJson

    return AnsibleExitJson
