#!/usr/bin/python
#
# Copyright (c) 2020-2023 Cisco and/or its affiliates.
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
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Praveen Ramoorthy"

DOCUMENTATION = """
---
module: dcnm_network
short_description: Add and remove custom Networks from a DCNM managed VXLAN fabric.
version_added: "4.0.0"
description:
    - "Add and remove custom Networks from a DCNM managed VXLAN fabric."
    - "In Multisite fabrics, Networks can be created only on Multisite fabric"
author: Praveen Ramoorthy(@praveenramoorthy)
options:
  fabric:
    description:
    - Name of the target fabric for network operations
    type: str
    required: yes
  state:
    description:
    - The state of DCNM after module completion.
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
      - query
    default: merged
  config:
    description:
    - List of details of networks being managed. Not required for state deleted
    type: list
    elements: dict
    suboptions:
      net_name:
        description:
        - Name of the network being managed
        type: str
        required: true
      vrf_name:
        description:
        - Name of the VRF to which the network belongs to
        - This field is required for L3 Networks.
        - VRF name should be specified as "NA" for L2 networks
        type: str
        required: true
      net_id:
        description:
        - ID of the network being managed
        - If not specified in the playbook, DCNM will auto-select an available net_id
        type: int
        required: false
      net_template:
        description:
        - Name of the config template to be used
        type: str
        default: 'Default_Network_Universal'
      net_extension_template:
        description:
        - Name of the extension config template to be used
        type: str
        default: 'Default_Network_Extension_Universal'
      network_template_config:
        description:
        - To specifiy the network specific values for the network being managed using
          the config params and values specified in the network template/extension template.
        type: list
        elements: dict
        suboptions:
          attach:
            description:
            - List of network attachment details
            type: list
            elements: dict
            suboptions:
              fabric:
                description:
                - Fabric name where the switch to attach is present
                type: str
                required: true
              serialNumber:
                description:
                - Serial number of the switch to be attached to network
                type: str
                required: true
              deployment:
                description:
                - To specify if the switch should be attached/detached to/from network
                type: bool
                default: true
              vlan:
                description:
                - VLAN ID for the attachment.
                type: int
                default: -1
              switchPorts:
                description:
                - List of switch ports to be attached to network
                type: list
                default: []
              torPorts:
                description:
                - List of TOR ports to be attached to network
                type: list
                elements: dict
                suboptions:
                  switch:
                    description:
                    - Name of the TOR switch to which the network is attached
                    type: str
                  ports:
                    description:
                    - List of TOR ports to be attached to network
                    type: list
                    default: ""
                default: ""
              detachSwitchPorts:
                description:
                - List of switch ports to be detached from network
                type: list
                default: []
              instanceValues:
                description:
                - Switch specific values for the attachment
                type: str
                default: ""
              deploy:
                description:
                - To specify if the attachment to network is to be deployed
                type: bool
                default: true
"""

EXAMPLES = """

# Example for creating a network using a Default_Network_Universal template
- name: Add a network to a fabric and attach a switch to it
  cisco.dcnm.dcnm_networkv2:
    fabric: vxlan-fabric
    state: merged
    config:
      - net_name: "net1"
        vrf_name: "vrf1"
        net_id: 100
        vlan_id: 100
        net_template: Default_Network_Universal
        net_extension_template: Default_Network_Extension_Universal
        # network_template_config block uses the config params and values specified in template specifed net_template
        # You should know the config params and values specified in the template.
        network_template_config:
          - gatewayIpAddress: "2.1.1.1/24"
            intfDescription: "test_interface"
            mtu: 1500
            secondaryGW1: "3.1.1.1"
            loopbackId: 10
            attach:
              - fabric: vxlan-fabric
                networkName: "net1"
                serialNumber: "FDO1234QWER"
                deployment: true
                vlan: 100
                switchPorts: "Ethernet1/1,Ethernett1/2"
                torPorts: "Tor1(Ethernet1/13),Tor2(Ethernet1/14)"
                instanceValues: ""
                deploy: true

"""

import json
import time
import copy
import re
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    get_fabric_inventory_details,
    dcnm_send,
    validate_list_of_dicts,
    dcnm_get_ip_addr_info,
    get_ip_sn_dict,
    get_fabric_details,
    get_ip_sn_fabric_dict,
    dcnm_version_supported,
    dcnm_get_url,
    build_arg_spec,
    get_diff,
)
from ansible.module_utils.basic import AnsibleModule


class DcnmNetworkv2:

    dcnm_network_paths = {
        12: {
            "GET_NET": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/v2/fabrics/{}/networks",
            "GET_NET_ATTACH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/v2/fabrics/{}/networks/attachments?network-names={}",
            "GET_NET_NAME": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/v2/fabrics/{}/networks/{}",
            "TEMPLATE_WITH_NAME": "/appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates/{}",
            "BULK_NET": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/v2/bulk-create/networks"

        },
    }

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))
        self.check_mode = False
        self.have_create = []
        self.want_create = []
        self.diff_create = []
        self.diff_create_update = []
        self.diff_not_w_in_h = []
        # This variable is created specifically to hold all the create payloads which are missing a
        # networkId. These payloads are sent to DCNM out of band (basically in the get_diff_merge())
        # We lose diffs for these without this variable. The content stored here will be helpful for
        # cases like "check_mode" and to print diffs[] in the output of each task.
        self.have_attach = []
        self.want_attach = []
        self.diff_attach = []
        self.diff_attach_update = []
        self.diff_attach_not_w_in_h = []
        self.validated = []
        # diff_detach is to list all attachments of a network being deleted, especially for state: OVERRIDDEN
        # The diff_detach and delete operations have to happen before create+attach+deploy for networks being created.
        # This is specifically to address cases where VLAN from a network which is being deleted is used for another
        # network. Without this additional logic, the create+attach+deploy go out first and complain the VLAN is already
        # in use.
        self.diff_detach = []
        self.have_deploy = {}
        self.want_deploy = {}
        self.diff_deploy = {}
        self.diff_undeploy = {}
        self.diff_delete = {}
        self.diff_input_format = []
        self.dyn_arg_spec = {}
        self.query = []
        self.dcnm_version = dcnm_version_supported(self.module)
        self.inventory_data = get_fabric_inventory_details(self.module, self.fabric)
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        self.ip_fab, self.sn_fab = get_ip_sn_fabric_dict(self.inventory_data)
        self.fabric_det = get_fabric_details(module, self.fabric)
        self.is_ms_fabric = (
            True if self.fabric_det.get("fabricType") == "MFD" else False
        )
        if self.dcnm_version < 12:
            self.module.fail_json(
                msg="dcnm_networkv2 module is only supported on NDFC. It is not support on DCNM"
            )
        else:
            self.paths = self.dcnm_network_paths[12]

        self.result = dict(changed=False, diff=[], response=[], warnings=[])

        self.failed_to_rollback = False
        self.WAIT_TIME_FOR_DELETE_LOOP = 5  # in seconds

    def get_diff_delete(self):

        diff_detach = []
        diff_undeploy = {}
        diff_delete = {}

        all_nets = ""

        if self.config:
            for want_c in self.want_create:
                if not next(
                    (
                        have_c
                        for have_c in self.have_create
                        if have_c["networkName"] == want_c["networkName"]
                    ),
                    None,
                ):
                    continue
                diff_delete.update({want_c["networkName"]: "DEPLOYED"})

                have_a = next(
                    (
                        attach
                        for attach in self.have_attach
                        if attach["networkName"] == want_c["networkName"]
                    ),
                    None,
                )

                if not have_a:
                    continue

                to_del = []
                atch_h = have_a["lanAttachList"]
                for a_h in atch_h:
                    if a_h["deployment"]:
                        a_h.update({"deployment": False})
                        a_h.update({"torPorts": ""})
                        a_h.update({"switchPorts": ""})
                        a_h.update({"detachSwitchPorts": ""})
                        to_del.append(a_h)
                        if diff_undeploy.get(a_h["serialNumber"]):
                            diff_undeploy[a_h["serialNumber"]].append(a_h["networkName"])
                        else:
                            diff_undeploy[a_h["serialNumber"]] = [a_h["networkName"]]
                if to_del:
                    have_a.update({"lanAttachList": to_del})
                    diff_detach.append(have_a)
        else:
            for have_a in self.have_attach:
                to_del = []
                atch_h = have_a["lanAttachList"]
                for a_h in atch_h:
                    if a_h["deployment"]:
                        a_h.update({"deployment": False})
                        a_h.update({"torPorts": ""})
                        a_h.update({"switchPorts": ""})
                        a_h.update({"detachSwitchPorts": ""})
                        to_del.append(a_h)
                        if diff_undeploy.get(a_h["serialNumber"]):
                            diff_undeploy[a_h["serialNumber"]].append(a_h["networkName"])
                        else:
                            diff_undeploy[a_h["serialNumber"]] = [a_h["networkName"]]
                if to_del:
                    have_a.update({"lanAttachList": to_del})
                    diff_detach.append(have_a)

                diff_delete.update({have_a["networkName"]: "DEPLOYED"})

        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

    def get_diff_override(self):

        diff_delete = {}

        warn_msg = self.get_diff_replace()

        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_detach = self.diff_detach
        diff_deploy = self.diff_deploy
        diff_undeploy = self.diff_undeploy

        for have_a in self.have_attach:
            # This block will take care of deleting all the networks that are only present on DCNM but not on playbook
            # The "if not found" block will go through all attachments under those networks and update them so that
            # they will be detached and also the network name will be added to delete payload.
            found = next(
                (
                    net
                    for net in self.want_create
                    if net["networkName"] == have_a["networkName"]
                ),
                None,
            )

            to_del = []
            if not found:
                atch_h = have_a["lanAttachList"]
                for a_h in atch_h:
                    if a_h["deployment"]:
                        a_h.update({"deployment": False})
                        a_h.update({"torPorts": ""})
                        a_h.update({"switchPorts": ""})
                        a_h.update({"detachSwitchPorts": ""})
                        to_del.append(a_h)
                        if diff_undeploy.get(a_h["serialNumber"]):
                            diff_undeploy[a_h["serialNumber"]].append(a_h["networkName"])
                        else:
                            diff_undeploy[a_h["serialNumber"]] = [a_h["networkName"]]

                if to_del:
                    have_a.update({"lanAttachList": to_del})
                    diff_detach.append(have_a)

                # The following is added just to help in deletion, we need to wait for detach transaction to complete
                # before attempting to delete the network.
                diff_delete.update({have_a["networkName"]: "DEPLOYED"})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete
        self.diff_detach = diff_detach
        return warn_msg
    
    def get_diff_replace(self):

        warn_msg = self.get_diff_merge(replace=True)
        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_deploy = self.diff_deploy

        for have_a in self.have_attach:
            r_net_list = []
            h_in_w = False
            for want_a in self.want_attach:
                # This block will take care of deleting any attachments that are present only on DCNM
                # but, not on the playbook. In this case, the playbook will have a network and few attaches under it,
                # but, the attaches may be different to what the DCNM has for the same network.
                if have_a["networkName"] == want_a["networkName"]:
                    h_in_w = True
                    atch_h = have_a["lanAttachList"]
                    atch_w = want_a.get("lanAttachList")

                    for a_h in atch_h:
                        if not a_h["deployment"]:
                            continue
                        a_match = False

                        if atch_w:
                            for a_w in atch_w:
                                if a_h["serialNumber"] == a_w["serialNumber"]:
                                    # Have is already in diff, no need to continue looking for it.
                                    a_match = True
                                    break
                        if not a_match:
                            a_h.update({"deployment": False})
                            a_h.update({"torPorts": ""})
                            a_h.update({"switchPorts": ""})
                            a_h.update({"detachSwitchPorts": ""})
                            r_net_list.append(a_h)
                            if diff_deploy.get(a_h["serialNumber"]):
                                diff_deploy[a_h["serialNumber"]].append(a_h["networkName"]) 
                            else:
                                diff_deploy[a_h["serialNumber"]] = [a_h["networkName"]]
                    break

            if not h_in_w:
                # This block will take care of deleting all the attachments which are in DCNM but
                # are not mentioned in the playbook. The playbook just has the network, but, does not have any attach
                # under it.
                found = next(
                    (
                        net
                        for net in self.want_create
                        if net["networkName"] == have_a["networkName"]
                    ),
                    None,
                )
                if found:
                    atch_h = have_a["lanAttachList"]
                    for a_h in atch_h:
                        if not a_h["deployment"]:
                            continue
                        a_h.update({"deployment": False})
                        a_h.update({"torPorts": ""})
                        a_h.update({"switchPorts": ""})
                        a_h.update({"detachSwitchPorts": ""})
                        r_net_list.append(a_h)
                        if diff_deploy.get(a_h["serialNumber"]):
                            diff_deploy[a_h["serialNumber"]].append(a_h["networkName"])
                        else:
                            diff_deploy[a_h["serialNumber"]] = [a_h["networkName"]]

            if r_net_list:
                in_diff = False
                for d_attach in self.diff_attach:
                    if have_a["networkName"] == d_attach["networkName"]:
                        in_diff = True
                        d_attach["lanAttachList"].extend(r_net_list)
                        break

                if not in_diff:
                    r_net_dict = {
                        "networkName": have_a["networkName"],
                        "lanAttachList": r_net_list,
                    }
                    diff_attach.append(r_net_dict)

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        return warn_msg
    
    def get_deploy_diff(self, diff_deploy):
            
        for w_deploy in self.want_deploy:
            if diff_deploy.get(w_deploy):
                for net in self.want_deploy[w_deploy]:
                    if net in diff_deploy[w_deploy]:
                        continue
                    else:
                        if diff_deploy.get(w_deploy):
                            diff_deploy[w_deploy].append(net)
                        else:
                            diff_deploy[w_deploy] = [net]
            elif self.have_deploy.get(w_deploy):
                for net in self.want_deploy[w_deploy]:
                    if net in self.have_deploy[w_deploy]:
                        continue
                    else:
                        if diff_deploy.get(w_deploy):
                            diff_deploy[w_deploy].append(net)
                        else:
                            diff_deploy[w_deploy] = [net]
            else:
                diff_deploy[w_deploy] = self.want_deploy[w_deploy]
                            
    def compute_deploy_diff(self, w_attach, diff_deploy):
        
        if self.want_deploy.get(w_attach["serialNumber"]):
            if w_attach["networkName"] in self.want_deploy[w_attach["serialNumber"]]:
                if diff_deploy.get(w_attach["serialNumber"]):
                    diff_deploy[w_attach["serialNumber"]].append(w_attach["networkName"])
                else:
                    diff_deploy[w_attach["serialNumber"]] = [w_attach["networkName"]]

    def get_attach_ports(self, w_attach, h_attach, replace=False):

        h_sw_ports = h_attach["switchPorts"]
        w_sw_ports = w_attach["switchPorts"]

        if sorted(h_sw_ports) != sorted(w_sw_ports):
            atch_sw_ports = list(
                set(w_sw_ports) - set(h_sw_ports)
            )
            w_attach.update(
                {
                    "switchPorts": ",".join(atch_sw_ports)
                    if atch_sw_ports
                    else ""
                }
            )

            if replace:
                dtach_sw_ports = list(
                    set(h_sw_ports) - set(w_sw_ports)
                )
                w_attach.update(
                    {
                        "detachSwitchPorts": ",".join(dtach_sw_ports)
                        if dtach_sw_ports
                        else ""
                    }
                )
        else:
            w_attach.update(
                {
                    "switchPorts": ",".join(w_sw_ports)
                    if w_sw_ports
                    else ""
                }
            )

    def get_attach_torports(self, w_attach, h_attach, replace=False):

        if w_attach.get("torPorts") != "":
            for tor_w in w_attach["torPorts"]:
                if h_attach.get("torPorts") != "":
                    for tor_h in h_attach["torPorts"]:
                        if tor_w["switch"] == tor_h["switch"]:
                            atch_tor_ports = []
                            h_tor_ports = tor_h["ports"]
                            w_tor_ports = tor_w["ports"]

                            if sorted(h_tor_ports) != sorted(w_tor_ports):
                                atch_tor_ports = list(
                                    set(w_tor_ports) - set(h_tor_ports)
                                )

                            if replace:
                                atch_tor_ports = w_tor_ports
                            else:
                                atch_tor_ports.extend(h_tor_ports)

                            torconfig = tor_w["switch"] + "(" + (",".join(atch_tor_ports)).strip() + ")"
                            w_attach.update({"torPorts": torconfig})
                else:
                    torconfig = tor_w["switch"] + "(" + (",".join(tor_w["ports"])).strip() + ")"
                    w_attach.update({"torPorts": torconfig})
        else:
            if replace:
                w_attach.update({"torPorts": ""})
            elif h_attach.get("torPorts") != "":
                for tor_h in h_attach.get("torPorts"):
                    torconfig = tor_h["switch"] + "(" + (",".join(tor_h["ports"])).strip() + ")"
                    w_attach.update({"torPorts": torconfig})
        
    def get_diff_merge(self, replace=False):

        diff_create = []
        diff_create_update = []
        diff_attach = []
        diff_deploy = {}
        warn_msg = None

        w_create, w_create_update, diff_not_w_in_h = get_diff(self.have_create, self.want_create)

        if w_create_update:
            diff_create_update.extend(w_create_update)
            for net in w_create_update:
                for attach in self.have_attach:
                    if net["networkName"] == attach["networkName"]:
                        for atch in attach.get("lanAttachList"):
                            if atch["deployment"]:
                                if diff_deploy.get(atch["serialNumber"]):
                                    diff_deploy[atch["serialNumber"]].append(atch["networkName"])
                                else:
                                    diff_deploy[atch["serialNumber"]] = [atch["networkName"]]

        if w_create:
            diff_create.extend(w_create)

        for want_a in self.want_attach:
            found = False
            for have_a in self.have_attach:
                if want_a["networkName"] == have_a["networkName"]:
                    found = True
                    w_attach, w_attach_update, diff_attach_not_w_in_h = get_diff(have_a["lanAttachList"], want_a["lanAttachList"])

                    if w_attach:
                        base = want_a.copy()
                        del base["lanAttachList"]
                        base.update({"lanAttachList": w_attach})
                        diff_attach.append(base)
                        for attach in w_attach:
                            self.compute_deploy_diff(attach, diff_deploy)

                    if w_attach_update:
                        base = want_a.copy()
                        del base["lanAttachList"]
                        for attach in w_attach_update:
                            for h_attach in have_a.get("lanAttachList"):
                                if attach["serialNumber"] == h_attach["serialNumber"]:
                                    self.get_attach_ports(attach, h_attach, replace)
                                    if h_attach["torPorts"] or attach["torPorts"]:
                                        self.get_attach_torports(attach, h_attach, replace)
                                    else:
                                        attach.update({"torPorts": ""})
                                    self.compute_deploy_diff(attach, diff_deploy)
                                    break
                        base.update({"lanAttachList": w_attach_update})
                        diff_attach.append(base)

            if not found and want_a.get("lanAttachList"):
                diff_attach.append(want_a)
                for attach in want_a.get("lanAttachList"):
                    attach.update(
                    {
                        "switchPorts": ",".join(attach["switchPorts"])
                        if attach.get("switchPorts")
                        else ""
                    }
                    )
                    if attach.get("torPorts"):
                        for tor_h in attach.get("torPorts"):
                            torconfig = tor_h["switch"] + "(" + (",".join(tor_h["ports"])).strip() + ")"
                            attach.update({"torPorts": torconfig})
                    self.compute_deploy_diff(attach, diff_deploy)

        self.get_deploy_diff(diff_deploy)
        self.diff_create = diff_create
        self.diff_create_update = diff_create_update
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        return warn_msg
    
    def get_diff_query(self):

        method = "GET"

        if self.config:
            query = []
            if self.have_create or self.have_attach:
                for want_c in self.want_create:
                    # Query the Network
                    item = {"Network": {}, "attach": []}
                    path = self.paths["GET_NET_NAME"].format(
                        self.fabric, want_c["networkName"]
                    )
                    network = dcnm_send(self.module, method, path)

                    if not network["DATA"]:
                        continue

                    net = network["DATA"]
                    if want_c["networkName"] == net["networkName"]:
                        item["Network"] = net
                        item["Network"]["networkTemplateConfig"] = net["networkTemplateConfig"]

                        # Query the Attachment for the found Networks
                        path = self.paths["GET_NET_ATTACH"].format(
                            self.fabric, want_c["networkName"]
                        )
                        net_attach_objects = dcnm_send(self.module, method, path)

                        if not net_attach_objects["DATA"]:
                            return

                        for net_attach in net_attach_objects["DATA"]:
                            if want_c["networkName"] == net_attach["networkName"]:
                                if not net_attach.get("lanAttachList"):
                                    continue
                                attach_list = net_attach["lanAttachList"]

                                for attach in attach_list:
                                    # append the attach network details
                                    item["attach"].append(attach)
                                query.append(item)

        else:
            query = []
            path = self.paths["GET_NET"].format(self.fabric)
            networks = dcnm_send(self.module, method, path)

            if not networks["DATA"]:
                return

            for net in networks["DATA"]:
                item = {"Network": {}, "attach": []}
                # append the network details
                item["Network"] = net
                item["Network"]["networkTemplateConfig"] = net["networkTemplateConfig"]

                # fetch the attachment for the network
                path = self.paths["GET_NET_ATTACH"].format(
                    self.fabric, net["networkName"]
                )
                net_attach_objects = dcnm_send(self.module, method, path)

                if not net_attach_objects["DATA"]:
                    return

                for net_attach in net_attach_objects["DATA"]:
                    if not net_attach.get("lanAttachList"):
                        continue
                    attach_list = net_attach["lanAttachList"]

                    for attach in attach_list:
                        # append the attach network details
                        item["attach"].append(attach)
                    query.append(item)

        self.query = query

    def get_have(self):

        have_create = []
        have_attach = []
        have_deploy = {}
        curr_networks = []

        state = self.params["state"]

        method = "GET"
        path = self.paths["GET_NET"].format(self.fabric)

        net_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(net_objects, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find Networks under fabric: {0}".format(self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
            return

        for net in net_objects["DATA"]:

            json_to_dict = net["networkTemplateConfig"]

            net.update({"networkTemplateConfig": json_to_dict})
            del net["displayName"]
            del net["serviceNetworkTemplate"]
            del net["source"]
            del net["tenantName"]
            del net["interfaceGroups"]
            del net["primaryNetworkId"]
            del net["type"]
            del net["primaryNetworkName"]
            del net["vlanId"]
            del net["hierarchicalKey"]
            del net["networkStatus"]

            curr_networks.append(net["networkName"])
            have_create.append(net)
        
        if not curr_networks:
            return
        
        net_attach_objects = dcnm_get_url(
            self.module,
            self.fabric,
            self.paths["GET_NET_ATTACH"],
            ",".join(curr_networks),
            "networks",
        )

        if not net_attach_objects["DATA"]:
            return

        for net_attach in net_attach_objects["DATA"]:
            if not net_attach.get("lanAttachList"):
                continue
            attach_list = net_attach["lanAttachList"]
            for attach in attach_list:
                deployment = attach["isLanAttached"]
                if ( not bool(deployment) or
                    attach["lanAttachState"] == "OUT-OF-SYNC"
                    or attach["lanAttachState"] == "PENDING"
                    or attach["lanAttachState"] == "FAILED"
                ):
                    deployed = False
                else:
                    deployed = True

                if deployed:
                    if have_deploy.get(attach["switchSerialNo"]):
                        have_deploy[attach["switchSerialNo"]].append(attach["networkName"])
                    else:
                        have_deploy[attach["switchSerialNo"]] = [attach["networkName"]]

                sn = attach["switchSerialNo"]
                vlan = attach["vlanId"]             
                hports = attach["portNames"]
                attach.update({"torPorts": ""})
                if attach["portNames"] and re.match(r"(\S+\(([Ee]thernet\d+\/\d+,?\s?)+\),?\s?)+", attach["portNames"]):
                    torlist = []
                    sw_ports_list = attach["portNames"]
                    tor_list = sw_ports_list.split(") ")
                    for idx, tor in enumerate(tor_list):
                        if tor:
                            torports = {}
                            sw_port = tor.split(")")
                            eth_list = sw_port[0].split("(")
                            # idx 0 has the switch ports configured
                            # idx 1 onwards has the tor ports configured
                            if idx == 0:
                                hports = eth_list[1]
                                ports = sorted(re.split(", |,", hports))
                                continue
                            else:
                                torports.update({"switch": eth_list[0]})
                                torports.update({"ports": sorted(re.split(", |,", eth_list[1]))})
                                torlist.append(torports)
                    torlist = sorted(torlist, key=lambda torlist: torlist['switch'])
                    attach.update({"torPorts": torlist})
                elif attach["portNames"]:
                    ports = sorted(re.split(", |,", hports))
                else:
                    ports = []
                    
                # The deletes and updates below are done to update the incoming dictionary format to
                # match to what the outgoing payload requirements mandate.
                # Ex: 'vlanId' in the attach section of incoming payload needs to be changed to 'vlan'
                # on the attach section of outgoing payload.

                if (state == "deleted" and
                    (attach["lanAttachState"] == "OUT-OF-SYNC" or attach["lanAttachState"] == "PENDING" or attach["lanAttachState"] == "FAILED")):
                    deployment = True

                del attach["vlanId"]
                del attach["switchSerialNo"]
                del attach["switchName"]
                del attach["switchRole"]
                del attach["ipAddress"]
                del attach["lanAttachState"]
                del attach["isLanAttached"]
                del attach["fabricName"]
                del attach["portNames"]
                del attach["switchDbId"]
                del attach["networkId"]
                del attach["entityName"]
                del attach["peerSerialNo"]

                if "displayName" in attach.keys():
                    del attach["displayName"]
                if "interfaceGroups" in attach.keys():
                    del attach["interfaceGroups"]

                attach.update({"fabric": self.fabric})
                attach.update({"vlan": vlan})
                attach.update({"serialNumber": sn})
                attach.update({"deployment": deployment})
                attach.update({"extensionValues": ""})
                attach.update({"instanceValues": ""})
                attach.update({"freeformConfig": ""})
                attach.update({"dot1QVlan": 1})
                attach.update({"detachSwitchPorts": ""})
                attach.update({"switchPorts": ports})
                attach.update({"untagged": False})

        have_attach = net_attach_objects["DATA"]

        self.have_create = have_create
        self.have_attach = have_attach
        self.have_deploy = have_deploy

    def update_create_params(self, net):

        if not net:
            return net

        state = self.params["state"]

        n_template = net.get("net_template", "Default_Network_Universal")
        ne_template = net.get(
            "net_extension_template", "Default_Network_Extension_Universal"
        )

        if state == "deleted" or state == "query":
            net_upd = {
                "fabric": self.fabric,
                "networkName": net["net_name"],
                "networkId": net["net_id"],
                "networkTemplate": n_template,
                "networkExtensionTemplate": ne_template,
            }
        else:
            net_upd = {
                "d_key": "networkName",
                "fabric": self.fabric,
                "vrf": net["vrf_name"],
                "networkName": net["net_name"],
                "networkId": net["net_id"],
                "networkTemplate": n_template,
                "networkExtensionTemplate": ne_template,
            }
            net_upd.update({"networkTemplateConfig": net["network_template_config"]})
            if not net_upd["networkTemplateConfig"]["trmEnabled"]:
                net_upd["networkTemplateConfig"]["igmpVersion"] = ""

        return net_upd

    def update_attach_params(self, attach, net_name):

        hports = []
        htorlist = []
        ports = []
        state = self.params["state"]

        if state == "deleted" or state == "query":
            return

        for atch_h in self.have_attach:
            if ( net_name == atch_h["networkName"]):
                hv_attach = atch_h["lanAttachList"]
                for h_attach in hv_attach:
                    if(attach["serialNumber"] == h_attach["serialNumber"]):
                        if attach["vlan"] == "-1":
                            attach.update({"vlan": h_attach["vlan"]})
                        if state == "merged" and h_attach["switchPorts"]:
                            hports = h_attach["switchPorts"]
                        if state == "merged" and h_attach["torPorts"]:
                            htorlist = h_attach["torPorts"]
                        break

        wports = sorted(attach["switchPorts"])
        if wports:
            if state == "merged" and hports:
                if wports != hports:
                    wports = list(set(wports) | set(hports))
                ports = sorted(wports)
            else:
                ports = wports
        elif state == "merged" and hports:
            ports = hports

        if attach["torPorts"]:
            for tor in attach["torPorts"]:
                torports = {}
                torlist = []
                for htor in htorlist:
                    if htor["switch"] == tor["switch"]:
                        if sorted(tor["ports"]) != sorted(htor["ports"]):
                            wtor_ports = list(set(tor["ports"]) | set(htor["ports"]))
                        else:
                            wtor_ports = tor["ports"]
                        wtor_ports = sorted(wtor_ports)
                        torports.update({"switch": tor["switch"]})
                        torports.update({"ports": wtor_ports})
                        torlist.append(torports)
                        torlist = sorted(torlist, key=lambda torlist: torlist['switch'])
                        break
                if torlist:
                    attach.update({"torPorts": torlist})
        else:
            if state == "merged" and htorlist:
                attach.update({"torPorts": htorlist})
            else:
                attach.update({"torPorts": ""})

        if attach["detachSwitchPorts"]:
            attach.update({"detachSwitchPorts": attach["detachSwitchPorts"]})
        else:
            attach.update({"detachSwitchPorts": ""})

        if ports:
            attach.update({"switchPorts": ports})
        else:
            attach.update({"switchPorts": ""})

        attach.update({"networkName": net_name})
        attach.update({"d_key": "serialNumber"})

    def get_want(self):

        want_create = []
        want_attach = []
        want_deploy = {}

        state = self.params["state"]

        if not self.config:
            return

        for net in self.validated:
            net_attach = {}
            networks = []

            want_create.append(self.update_create_params(net))

            if not net.get("attach") or state == "deleted" or state == "query":
                continue

            for attach in net["attach"]:
                self.update_attach_params(attach, net["net_name"])
                networks.append(attach)
                if attach["deploy"]:
                    if want_deploy.get(attach["serialNumber"]):
                        want_deploy[attach["serialNumber"]].append(attach["networkName"])
                    else:
                        want_deploy[attach["serialNumber"]] = [attach["networkName"]]
                del attach["deploy"]

            net_attach.update({"networkName": net["net_name"]})
            net_attach.update({"lanAttachList": networks})
            want_attach.append(net_attach)

        self.want_create = want_create
        self.want_attach = want_attach
        self.want_deploy = want_deploy

    def wait_for_del_ready(self):

        method = "GET"
        if self.diff_delete:
            for net in self.diff_delete:
                state = False
                path = self.paths["GET_NET_ATTACH"].format(self.fabric, net)
                iter = 0
                while not state:
                    resp = dcnm_send(self.module, method, path)
                    state = True
                    iter+=1
                    if resp["DATA"]:
                        attach_list = resp["DATA"][0]["lanAttachList"]
                        for atch in attach_list:
                            if (
                                atch["lanAttachState"] == "OUT-OF-SYNC"
                                or atch["lanAttachState"] == "FAILED"
                            ):
                                if iter<10:
                                    self.diff_delete.update({net: "DEPLOYED"})
                                    state = False
                                    time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                                else:
                                    self.diff_delete.update({net: "OUT-OF-SYNC"})
                                break
                            if atch["lanAttachState"] != "NA":
                                self.diff_delete.update({net: "DEPLOYED"})
                                state = False
                                time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                                break
                            self.diff_delete.update({net: "NA"})

            return True

    def update_ms_fabric(self, diff):
        if not self.is_ms_fabric:
            return

        for list_elem in diff:
            for node in list_elem["lanAttachList"]:
                node["fabric"] = self.sn_fab[node["serialNumber"]]
    
    def push_to_remote_update(self, path, is_rollback=False):

        method = "PUT"

        for net in self.diff_create_update:
            update_path = path + "/{0}".format(net["networkName"])
            resp = dcnm_send(self.module, method, update_path, json.dumps(net))
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "create")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

    def push_to_remote_detach(self, path, is_rollback=False):
        
        method = "POST"

        detach_path = path + "/attachments"

        # Update the fabric name to specific fabric which the switches are part of.
        self.update_ms_fabric(self.diff_detach)

        for d_a in self.diff_detach:
            for v_a in d_a["lanAttachList"]:
                if v_a.get("d_key") is not None:
                    del v_a["d_key"]

        resp = dcnm_send(
            self.module, method, detach_path, json.dumps(self.diff_detach)
        )
        self.result["response"].append(resp)
        fail, self.result["changed"] = self.handle_response(resp, "attach")
        if fail:
            if is_rollback:
                self.failed_to_rollback = True
                return
            self.failure(resp)

        time.sleep(10)

    def push_to_remote_undeploy(self, is_rollback=False):

        method = "POST"

        deploy_path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/v2/networks/deploy"
        for value in self.diff_undeploy:
            self.diff_undeploy[value] = ",".join(self.diff_undeploy[value])

        resp = dcnm_send(
            self.module, method, deploy_path, json.dumps(self.diff_undeploy)
        )
        # Use the self.wait_for_del_ready() function to refresh the state
        # of self.diff_delete dict and re-attempt the undeploy action if
        # the state of the network is "OUT-OF-SYNC"
        # self.wait_for_del_ready()
        # for net, state in self.diff_delete.items():
        #     if state == "OUT-OF-SYNC":
        #         resp = dcnm_send(
        #             self.module, method, deploy_path, json.dumps(self.diff_undeploy)
        #         )

        self.result["response"].append(resp)
        fail, self.result["changed"] = self.handle_response(resp, "deploy")
        if fail:
            if is_rollback:
                self.failed_to_rollback = True
                return
            self.failure(resp)

    def push_to_remote_delete(self, path, is_rollback=False):

        method = "DELETE"
        del_failure = ""
        resp = ""

        if self.wait_for_del_ready():
            for net, state in self.diff_delete.items():
                # if state == "OUT-OF-SYNC":
                #     del_failure += net + ","
                #     continue
                delete_path = path + "/" + net
                resp = dcnm_send(self.module, method, delete_path)
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "delete")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)
            
        if del_failure:
            fail_msg = "Deletion of Networks {0} has failed: {1}".format(del_failure[:-1], resp)
            self.result["response"].append(resp)
            if is_rollback:
                self.failed_to_rollback = True
                return
            self.failure(fail_msg)

    def push_to_remote_create(self, path, is_rollback=False):

        for net in self.diff_create:
            json_to_dict = net["networkTemplateConfig"]
            net.update({"networkTemplateConfig": json_to_dict})

        method = "POST"
        bulk_path = self.paths["BULK_NET"]
        resp = dcnm_send(self.module, method, bulk_path, json.dumps(self.diff_create))
        self.result["response"].append(resp)
        fail, self.result["changed"] = self.handle_response(resp, "create")
        if fail:
            if is_rollback:
                self.failed_to_rollback = True
                return
            self.failure(resp)

    def push_to_remote_attach(self, path, is_rollback=False):

        method = "POST"
        attach_path = path + "/attachments"

        # Update the fabric name to specific fabric which the switches are part of.
        self.update_ms_fabric(self.diff_attach)

        for d_a in self.diff_attach:
            for v_a in d_a["lanAttachList"]:
                if v_a.get("d_key") is not None:
                    del v_a["d_key"]

        for attempt in range(0, 50):
            resp = dcnm_send(
                self.module, method, attach_path, json.dumps(self.diff_attach)
            )
            update_in_progress = False
            for key in resp["DATA"].keys():
                if re.search(
                    r"Failed.*Please try after some time", str(resp["DATA"][key])
                ):
                    update_in_progress = True
            if update_in_progress:
                time.sleep(1)
                continue

            break
        self.result["response"].append(resp)
        fail, self.result["changed"] = self.handle_response(resp, "attach")
        # If we get here and an update_in_progress is True then
        # not all of the attachments were successful which represents a
        # failure condition.
        if fail or update_in_progress:
            if is_rollback:
                self.failed_to_rollback = True
                return
            self.failure(resp)

        time.sleep(10)

    def push_to_remote_deploy(self, is_rollback=False):

        method = "POST"

        deploy_path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/v2/networks/deploy"
        for value in self.diff_deploy:
            self.diff_deploy[value] = ",".join(self.diff_deploy[value])
        resp = dcnm_send(
            self.module, method, deploy_path, json.dumps(self.diff_deploy)
        )
        self.result["response"].append(resp)
        fail, self.result["changed"] = self.handle_response(resp, "deploy")
        if fail:
            if is_rollback:
                self.failed_to_rollback = True
                return
            self.failure(resp)

    def push_to_remote(self, is_rollback=False):

        path = self.paths["GET_NET"].format(self.fabric)

        if self.diff_create_update:
            self.push_to_remote_update(path, is_rollback)
            
        #
        # The detach and un-deploy operations are executed before the create,attach and deploy to particularly
        # address cases where a VLAN of a network being deleted is re-used on a new network being created. This is
        # needed specially for state: overridden
        #

        if self.diff_detach:
            self.push_to_remote_detach(path, is_rollback)

        if self.diff_undeploy:
            self.push_to_remote_undeploy(is_rollback)

        if self.diff_delete:
            self.push_to_remote_delete(path, is_rollback)

        if self.diff_create:
            self.push_to_remote_create(path, is_rollback)

        if self.diff_attach:
            self.push_to_remote_attach(path, is_rollback)

        if self.diff_deploy:
            self.push_to_remote_deploy(is_rollback)

    def get_arg_spec(self, net):

        template_name = net.get("net_extension_template", False)
        ext_template_name = net.get("net_template", False)
        net_uni_dyn_spec = {}
        net_ext_dyn_spec = {}

        if self.dyn_arg_spec.get(template_name):
            net_uni_dyn_spec = self.dyn_arg_spec[template_name]
        else:
            path = self.paths["TEMPLATE_WITH_NAME"].format(template_name)
            net_uni_dyn_spec = build_arg_spec(self.module, path)
            self.dyn_arg_spec.update({template_name: net_uni_dyn_spec})

        if self.dyn_arg_spec.get(ext_template_name):
            net_ext_dyn_spec = self.dyn_arg_spec[ext_template_name]
        else:
            path = self.paths["TEMPLATE_WITH_NAME"].format(ext_template_name)
            net_ext_dyn_spec = build_arg_spec(self.module, path)
            self.dyn_arg_spec.update({ext_template_name: net_ext_dyn_spec})

        net_dyn_spec =  {**net_ext_dyn_spec, **net_uni_dyn_spec}
        return net_dyn_spec

    def validate_input(self):
        """Parse the playbook values, validate to param specs."""

        state = self.params["state"]

        net_static_spec = dict(
            net_name=dict(required=True, type="str", length_max=64),
            net_id=dict(required=True, type="int", range_max=16777214),
            vrf_name=dict(required=True, type="str", length_max=32),
            net_template=dict(type="str", default="Default_Network_Universal"),
            net_extension_template=dict(
                type="str", default="Default_Network_Extension_Universal"
            ),
            network_template_config=dict(type="list")
        )

        net_attach_spec = dict(
            deployment=dict(type="bool", default=False),
            detachSwitchPorts=dict(type="list", default=[]),
            dot1QVlan=dict(type="int", default="1"),
            extensionValues=dict(type="string", default=""),
            fabric=dict(type="str", default=""),
            freeformConfig=dict(type="string", default=""),
            serialNumber=dict(required=True, type="string", default=""),
            switchPorts=dict(type="list", default=[]),
            torPorts=dict(type="list", default=[], elements="dict"),
            untagged=dict(type="bool", default=False),
            vlan=dict(type="int", default="-1"),
            deploy=dict(type="bool", default=True),
        )

        tor_att_spec = dict(
            switch=dict(required=True, type="str"),
            ports=dict(required=False, type="list", default=[]),
        )

        if self.config:
            msg = None
            # Validate net params
            valid_net, invalid_params = validate_list_of_dicts(
                self.config, net_static_spec
            )

            if invalid_params:
                msg = "Invalid parameters in playbook: {0}".format(
                    "\n".join(invalid_params)
                )
                self.module.fail_json(msg=msg)

            if state == "deleted" or state == "query":
                self.validated = valid_net
                return

            for net in valid_net:
                att_present=False
                net_dyn_spec = self.get_arg_spec(net)
                if net.get("network_template_config"):
                    if net["network_template_config"][0].get("attach"):
                        valid_att, invalid_att = validate_list_of_dicts(
                            net["network_template_config"][0]["attach"], net_attach_spec
                        )
                        invalid_params.extend(invalid_att)
                        att_present=True

                    valid_dyn_net, invalid_net = validate_list_of_dicts(
                        net["network_template_config"], net_dyn_spec
                    )
                    invalid_params.extend(invalid_net)
                    net["network_template_config"] = valid_dyn_net[0]
                    if net["network_template_config"]["mcastGroup"] == "":
                        net["network_template_config"]["mcastGroup"] = "239.1.1.1"
                    
                    if att_present:
                        net["attach"] = valid_att
                        for attach in net["attach"]:
                            if attach.get("ports"):
                                attach["ports"] = [port.capitalize() for port in attach["ports"]]
                            if attach.get("torPorts"):
                                valid_tor, invalid_tor = validate_list_of_dicts(
                                    attach["torPorts"], tor_att_spec
                                )
                                invalid_params.extend(invalid_tor)
                                attach["torPorts"] = valid_tor
                                for tor in attach["torPorts"]:
                                    if tor.get("ports"):
                                        tor["ports"] = [port.capitalize() for port in tor["ports"]]
                            else:
                                attach["torPorts"] = []

                self.validated.append(net)

            if invalid_params:
                msg = "Invalid parameters in playbook: {0}".format(
                    "\n".join(invalid_params)
                )
                self.module.fail_json(msg=msg)

    def format_diff(self):

        diff = []

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_update = copy.deepcopy(self.diff_create_update)
        diff_attach = copy.deepcopy(self.diff_attach)
        diff_detach = copy.deepcopy(self.diff_detach)
        diff_deploy = copy.deepcopy(self.diff_deploy)
        diff_undeploy = copy.deepcopy(self.diff_undeploy)

        diff_create.extend(diff_create_update)
        diff_attach.extend(diff_detach)

        for want_d in diff_create:

            found_a = next(
                (
                    net
                    for net in diff_attach
                    if net["networkName"] == want_d["networkName"]
                ),
                None,
            )

            found_c = want_d
            found_c.update({"net_name": found_c["networkName"]})
            found_c.update({"vrf_name": found_c.get("vrf", "NA")})
            found_c.update({"net_id": found_c["networkId"]})
            found_c.update({"net_template": found_c["networkTemplate"]})
            found_c.update(
                {"net_extension_template": found_c["networkExtensionTemplate"]}
            )
            found_c.update({"attach": []})

            del found_c["fabric"]
            del found_c["networkName"]
            del found_c["networkId"]
            del found_c["networkTemplate"]
            del found_c["networkExtensionTemplate"]
            del found_c["vrf"]
            del found_c["d_key"]

            if found_a:
                attach = found_a.get("lanAttachList")
                found_c["attach"].append(attach)

            diff.append(found_c)

        self.diff_input_format = diff

    def handle_response(self, resp, op):

        fail = False
        changed = True

        res = resp.copy()

        if op == "query_dcnm":
            # This if blocks handles responses to the query APIs against DCNM.
            # Basically all GET operations.
            #
            if res.get("ERROR") == "Not Found" and res["RETURN_CODE"] == 404:
                return True, False
            if res["RETURN_CODE"] != 200 or res["MESSAGE"] != "OK":
                return False, True
            return False, False

        # Responses to all other operations POST and PUT are handled here.
        if res.get("MESSAGE") != "OK" or res["RETURN_CODE"] != 200:
            fail = True
            changed = False
            return fail, changed
        if res.get("ERROR"):
            fail = True
            changed = False
        if op == "attach" and "is in use already" in str(res.values()):
            fail = True
            changed = False
        if op == "attach" and "Invalid interfaces" in str(res.values()):
            fail = True
            changed = True
        if op == "deploy" and "No switches PENDING for deployment" in str(res.values()):
            changed = False

        return fail, changed
    
    def failure(self, resp):

        # # Donot Rollback for Multi-site fabrics
        # if self.is_ms_fabric:
        #     self.failed_to_rollback = True
        #     self.module.fail_json(msg=resp)
        #     return

        # # Implementing a per task rollback logic here so that we rollback DCNM to the have state
        # # whenever there is a failure in any of the APIs.
        # # The idea would be to run overridden state with want=have and have=dcnm_state
        # self.want_create = self.have_create
        # self.want_attach = self.have_attach
        # self.want_deploy = self.have_deploy

        # self.have_create = []
        # self.have_attach = []
        # self.have_deploy = {}
        # self.get_have()
        # self.get_diff_override()

        # self.push_to_remote(True)

        # if self.failed_to_rollback:
        #     msg1 = "FAILED - Attempted rollback of the task has failed, may need manual intervention"
        # else:
        #     msg1 = "SUCCESS - Attempted rollback of the task has succeeded"

        # res = copy.deepcopy(resp)
        # if isinstance(res, str):
        #     self.module.fail_json(msg=res)

        # res.update({"ROLLBACK_RESULT": msg1})

        # if not resp.get("DATA"):
        #     data = copy.deepcopy(resp.get("DATA"))
        #     if data.get("stackTrace"):
        #         data.update(
        #             {"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"}
        #         )
        #         res.update({"DATA": data})

        # if self.module._verbosity >= 5:
        #     self.module.fail_json(msg=res)

        self.module.fail_json(msg=resp)


def main():
    """main entry point for module execution"""

    element_spec = dict(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict"),
        state=dict(
            default="merged",
            choices=["merged", "replaced", "deleted", "overridden", "query"],
        ),
    )

    module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    dcnm_netv2 = DcnmNetworkv2(module)

    if not dcnm_netv2.ip_sn:
        module.fail_json(
            msg="Fabric {0} missing on DCNM or does not have any switches".format(
                dcnm_netv2.fabric
            )
        )

    dcnm_netv2.validate_input()
    dcnm_netv2.get_have()
    dcnm_netv2.get_want()

    warn_msg = None

    if module.params["state"] == "merged":
        warn_msg = dcnm_netv2.get_diff_merge()

    if module.params["state"] == "replaced":
        warn_msg = dcnm_netv2.get_diff_replace()

    if module.params["state"] == "overridden":
        warn_msg = dcnm_netv2.get_diff_override()

    if module.params["state"] == "deleted":
        dcnm_netv2.get_diff_delete()

    if module.params["state"] == "query":
        dcnm_netv2.get_diff_query()
        dcnm_netv2.result["response"] = dcnm_netv2.query

    dcnm_netv2.result["warnings"].append(warn_msg) if warn_msg else []

    if (
        dcnm_netv2.diff_create
        or dcnm_netv2.diff_attach
        or dcnm_netv2.diff_deploy
        or dcnm_netv2.diff_delete
        or dcnm_netv2.diff_create_update
        or dcnm_netv2.diff_detach
        or dcnm_netv2.diff_undeploy
    ):
        dcnm_netv2.result["changed"] = True
    else:
        dcnm_netv2.result["changed"] = False
        module.exit_json(**dcnm_netv2.result)

    dcnm_netv2.format_diff()
    dcnm_netv2.result["diff"] = dcnm_netv2.diff_input_format

    if module.check_mode:
        dcnm_netv2.result["changed"] = False
        module.exit_json(**dcnm_netv2.result)

    dcnm_netv2.push_to_remote()

    module.exit_json(**dcnm_netv2.result)


if __name__ == "__main__":
    main()
