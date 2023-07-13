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
__author__ = "Chris Van Heuveln, Shrishail Kariyappanavar, Karthik Babu Harichandra Babu, Praveen Ramoorthy"

DOCUMENTATION = """
---
module: dcnm_network
short_description: Add and remove Networks from a DCNM managed VXLAN fabric.
version_added: "0.9.0"
description:
    - "Add and remove Networks from a DCNM managed VXLAN fabric."
    - "In Multisite fabrics, Networks can be created only on Multisite fabric"
author: Chris Van Heuveln(@chrisvanheuveln), Shrishail Kariyappanavar(@nkshrishail) Praveen Ramoorthy(@praveenramoorthy)
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
        - This field is required for L3 Networks. VRF name should not be specified
          or may be specified as "" for L2 networks
        type: str
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
      vlan_id:
        description:
        - VLAN ID for the network.
        - If not specified in the playbook, DCNM will auto-select an available vlan_id
        type: int
        required: false
      routing_tag:
        description:
        - Routing Tag for the network profile
        type: int
        required: false
        default: 12345
      gw_ip_subnet:
        description:
        - Gateway with subnet for the network
        type: str
        required: false
      is_l2only:
        description:
        - Layer 2 only network
        - If specified as true, VRF Name(vrf_name) should not be specified or can be
          specified as ""
        type: bool
        required: false
        default: false
      vlan_name:
        description:
        - Name of the vlan configured
        - if > 32 chars enable, system vlan long-name on switch
        type: str
        required: false
      int_desc:
        description:
        - Description for the interface
        type: str
        required: false
      mtu_l3intf:
        description:
        - MTU for Layer 3 interfaces
        - Configured MTU value should be in range 68-9216
        type: int
        required: false
      arp_suppress:
        description:
        - ARP suppression
        - ARP suppression is only supported if SVI is present when Layer-2-Only is not enabled
        type: bool
        required: false
        default: false
      dhcp_srvr1_ip:
        description:
        - DHCP relay IP address of the first DHCP server
        type: str
        required: false
      dhcp_srvr1_vrf:
        description:
        - VRF ID of first DHCP server
        type: str
        required: false
      dhcp_srvr2_ip:
        description:
        - DHCP relay IP address of the second DHCP server
        type: str
        required: false
      dhcp_srvr2_vrf:
        description:
        - VRF ID of second DHCP server
        type: str
        required: false
      dhcp_srvr3_ip:
        description:
        - DHCP relay IP address of the third DHCP server
        type: str
        required: false
      dhcp_srvr3_vrf:
        description:
        - VRF ID of third DHCP server
        type: str
        required: false
      dhcp_loopback_id:
        description:
        - Loopback ID for DHCP Relay interface
        - Configured ID value should be in range 0-1023
        type: int
        required: false
      multicast_group_address:
        description:
        - The multicast IP address for the network
        type: str
        required: false
      gw_ipv6_subnet:
        description:
        - IPv6 Gateway with prefix for the network
        type: str
        required: false
      secondary_ip_gw1:
        description:
        - IP address with subnet for secondary gateway 1
        type: str
        required: false
      secondary_ip_gw2:
        description:
        - IP address with subnet for secondary gateway 2
        type: str
        required: false
      secondary_ip_gw3:
        description:
        - IP address with subnet for secondary gateway 3
        type: str
        required: false
      secondary_ip_gw4:
        description:
        - IP address with subnet for secondary gateway 4
        type: str
        required: false
      trm_enable:
        description:
        - Enable Tenant Routed Multicast
        type: bool
        required: false
        default: false
      route_target_both:
        description:
        - Enable both L2 VNI Route-Target
        type: bool
        required: false
        default: false
      l3gw_on_border:
        description:
        - Enable L3 Gateway on Border
        type: bool
        required: false
        default: false
      netflow_enable:
        description:
        - Enable Netflow
        - Netflow is supported only if it is enabled on fabric
        - Netflow configs are supported on NDFC only
        type: bool
        required: false
        default: false
      intfvlan_nf_monitor:
        description:
        - Interface Vlan Netflow Monitor
        - Applicable only if 'Layer 2 Only' is not enabled. Provide monitor name defined in fabric setting for Layer 3 Record
        - Netflow configs are supported on NDFC only
        type: str
        required: false
      vlan_nf_monitor:
        description:
        - Vlan Netflow Monitor
        - Provide monitor name defined in fabric setting for Layer 3 Record
        - Netflow configs are supported on NDFC only
        type: str
        required: false
      attach:
        description:
        - List of network attachment details
        type: list
        elements: dict
        suboptions:
          ip_address:
            description:
            - IP address of the switch where the network will be attached or detached
            type: str
            required: true
          ports:
            description:
            - List of switch interfaces where the network will be attached
            type: list
            elements: str
            required: true
          deploy:
            description:
            - Per switch knob to control whether to deploy the attachment
            - This knob has been deprecated from Ansible NDFC Collection Version 2.1.0 onwards.
              There will not be any functional impact if specified in playbook.
            type: bool
            default: true
      deploy:
        description:
        - Global knob to control whether to deploy the attachment
        - Ansible NDFC Collection Behavior for Version 2.0.1 and earlier
        - This knob will create and deploy the attachment in DCNM only when set to "True" in playbook
        - Ansible NDFC Collection Behavior for Version 2.1.0 and later
        - Attachments specified in the playbook will always be created in DCNM.
          This knob, when set to "True",  will deploy the attachment in DCNM, by pushing the configs to switch.
          If set to "False", the attachments will be created in DCNM, but will not be deployed
        type: bool
        default: true
"""

EXAMPLES = """
# This module supports the following states:
#
# Merged:
#   Networks defined in the playbook will be merged into the target fabric.
#     - If the network does not exist it will be added.
#     - If the network exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Networks that are not specified in the playbook will be untouched.
#
# Replaced:
#   Networks defined in the playbook will be replaced in the target fabric.
#     - If the Networks does not exist it will be added.
#     - If the Networks exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - Networks that are not specified in the playbook will be untouched.
#
# Overridden:
#   Networks defined in the playbook will be overridden in the target fabric.
#     - If the Networks does not exist it will be added.
#     - If the Networks exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - Networks that are not specified in the playbook will be deleted.
#
# Deleted:
#   Networks defined in the playbook will be deleted.
#   If no Networks are provided in the playbook, all Networks present on that DCNM fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the Networks listed in the playbook.

- name: Merge networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: merged
    config:
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
      attach:
      - ip_address: 192.168.1.224
        ports: [Ethernet1/13, Ethernet1/14]
      - ip_address: 192.168.1.225
        ports: [Ethernet1/13, Ethernet1/14]
      deploy: true
    - net_name: ansible-net12
      vrf_name: Tenant-2
      net_id: 7002
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 151
      gw_ip_subnet: '192.168.40.1/24'
      attach:
      - ip_address: 192.168.1.224
        ports: [Ethernet1/11, Ethernet1/12]
      - ip_address: 192.168.1.225
        ports: [Ethernet1/11, Ethernet1/12]
      deploy: false

- name: Replace networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: replaced
    config:
      - net_name: ansible-net13
        vrf_name: Tenant-1
        net_id: 7005
        net_template: Default_Network_Universal
        net_extension_template: Default_Network_Extension_Universal
        vlan_id: 150
        gw_ip_subnet: '192.168.30.1/24'
        attach:
        - ip_address: 192.168.1.224
          # Replace the ports with new ports
          # ports: [Ethernet1/13, Ethernet1/14]
          ports: [Ethernet1/16, Ethernet1/17]
          # Delete this attachment
        # - ip_address: 192.168.1.225
        #   ports: [Ethernet1/13, Ethernet1/14]
        deploy: true
        # Dont touch this if its present on DCNM
        # - net_name: ansible-net12
        #   vrf_name: Tenant-2
        #   net_id: 7002
        #   net_template: Default_Network_Universal
        #   net_extension_template: Default_Network_Extension_Universal
        #   vlan_id: 151
        #   gw_ip_subnet: '192.168.40.1/24'
        #   attach:
        #     - ip_address: 192.168.1.224
        #       ports: [Ethernet1/11, Ethernet1/12]
        #     - ip_address: 192.168.1.225
        #       ports: [Ethernet1/11, Ethernet1/12]
        #   deploy: false

- name: Override networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: overridden
    config:
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
      attach:
      - ip_address: 192.168.1.224
        # Replace the ports with new ports
        # ports: [Ethernet1/13, Ethernet1/14]
        ports: [Ethernet1/16, Ethernet1/17]
        # Delete this attachment
        # - ip_address: 192.168.1.225
        #   ports: [Ethernet1/13, Ethernet1/14]
      deploy: true
      # Delete this network
      # - net_name: ansible-net12
      #   vrf_name: Tenant-2
      #   net_id: 7002
      #   net_template: Default_Network_Universal
      #   net_extension_template: Default_Network_Extension_Universal
      #   vlan_id: 151
      #   gw_ip_subnet: '192.168.40.1/24'
      #   attach:
      #   - ip_address: 192.168.1.224
      #     ports: [Ethernet1/11, Ethernet1/12]
      #   - ip_address: 192.168.1.225
      #     ports: [Ethernet1/11, Ethernet1/12]
      #   deploy: false

- name: Delete selected networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: deleted
    config:
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
    - net_name: ansible-net12
      vrf_name: Tenant-2
      net_id: 7002
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 151
      gw_ip_subnet: '192.168.40.1/24'
      deploy: false

- name: Delete all the networkss
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: deleted

- name: Query Networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: query
    config:
    - net_name: ansible-net13
    - net_name: ansible-net12
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
)
from ansible.module_utils.basic import AnsibleModule


class DcnmNetwork:

    dcnm_network_paths = {
        11: {
            "GET_VRF": "/rest/top-down/fabrics/{}/vrfs",
            "GET_VRF_NET": "/rest/top-down/fabrics/{}/networks?vrf-name={}",
            "GET_NET_ATTACH": "/rest/top-down/fabrics/{}/networks/attachments?network-names={}",
            "GET_NET_ID": "/rest/managed-pool/fabrics/{}/segments/ids",
            "GET_NET": "/rest/top-down/fabrics/{}/networks",
            "GET_NET_NAME": "/rest/top-down/fabrics/{}/networks/{}",
            "GET_VLAN": "/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_NETWORK_VLAN",
        },
        12: {
            "GET_VRF": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs",
            "GET_VRF_NET": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks?vrf-name={}",
            "GET_NET_ATTACH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks/attachments?network-names={}",
            "GET_NET_ID": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/netinfo",
            "GET_NET": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks",
            "GET_NET_NAME": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks/{}",
            "GET_VLAN": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_NETWORK_VLAN",
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
        # This variable is created specifically to hold all the create payloads which are missing a
        # networkId. These payloads are sent to DCNM out of band (basically in the get_diff_merge())
        # We lose diffs for these without this variable. The content stored here will be helpful for
        # cases like "check_mode" and to print diffs[] in the output of each task.
        self.diff_create_quick = []
        self.have_attach = []
        self.want_attach = []
        self.diff_attach = []
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
        self.query = []
        self.dcnm_version = dcnm_version_supported(self.module)
        self.inventory_data = get_fabric_inventory_details(self.module, self.fabric)
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        self.ip_fab, self.sn_fab = get_ip_sn_fabric_dict(self.inventory_data)
        self.fabric_det = get_fabric_details(module, self.fabric)
        self.is_ms_fabric = (
            True if self.fabric_det.get("fabricType") == "MFD" else False
        )
        if self.dcnm_version > 12:
            self.paths = self.dcnm_network_paths[12]
        else:
            self.paths = self.dcnm_network_paths[self.dcnm_version]

        self.result = dict(changed=False, diff=[], response=[], warnings=[])

        self.failed_to_rollback = False
        self.WAIT_TIME_FOR_DELETE_LOOP = 5  # in seconds

    def diff_for_attach_deploy(self, want_a, have_a, replace=False):

        attach_list = []

        if not want_a:
            return attach_list

        dep_net = False
        for want in want_a:
            found = False
            if have_a:
                for have in have_a:
                    if want["serialNumber"] == have["serialNumber"]:
                        found = True

                        if want.get("isAttached") is not None:
                            if bool(have["isAttached"]) and bool(want["isAttached"]):
                                h_sw_ports = (
                                    have["switchPorts"].split(",")
                                    if have["switchPorts"]
                                    else []
                                )
                                w_sw_ports = (
                                    want["switchPorts"].split(",")
                                    if want["switchPorts"]
                                    else []
                                )

                                # This is needed to handle cases where vlan is updated after deploying the network
                                # and attachments. This ensures that the attachments before vlan update will use previous
                                # vlan id. All the active attachments on DCNM will have a vlan-id.
                                if have.get("vlan"):
                                    want["vlan"] = have.get("vlan")

                                if sorted(h_sw_ports) != sorted(w_sw_ports):
                                    atch_sw_ports = list(
                                        set(w_sw_ports) - set(h_sw_ports)
                                    )

                                    # Adding some logic which is needed for replace and override.
                                    if replace:
                                        dtach_sw_ports = list(
                                            set(h_sw_ports) - set(w_sw_ports)
                                        )

                                        if not atch_sw_ports and not dtach_sw_ports:
                                            continue

                                        want.update(
                                            {
                                                "switchPorts": ",".join(atch_sw_ports)
                                                if atch_sw_ports
                                                else ""
                                            }
                                        )
                                        want.update(
                                            {
                                                "detachSwitchPorts": ",".join(
                                                    dtach_sw_ports
                                                )
                                                if dtach_sw_ports
                                                else ""
                                            }
                                        )

                                        del want["isAttached"]
                                        attach_list.append(want)
                                        if bool(want["is_deploy"]):
                                            dep_net = True

                                        continue

                                    if not atch_sw_ports:
                                        # The attachments in the have consist of attachments in want and more.
                                        continue

                                    want.update(
                                        {"switchPorts": ",".join(atch_sw_ports)}
                                    )
                                    del want["isAttached"]
                                    attach_list.append(want)
                                    if bool(want["is_deploy"]):
                                        dep_net = True
                                    continue

                            if bool(have["isAttached"]) is not bool(want["isAttached"]):
                                # When the attachment is to be detached and undeployed, ignore any changes
                                # to the attach section in the want(i.e in the playbook).

                                if not bool(want["isAttached"]):
                                    del have["isAttached"]
                                    have.update({"deployment": False})
                                    attach_list.append(have)
                                    if bool(want["is_deploy"]):
                                        dep_net = True
                                    continue
                                del want["isAttached"]
                                want.update({"deployment": True})
                                attach_list.append(want)
                                if bool(want["is_deploy"]):
                                    dep_net = True
                                continue

                        if bool(have["deployment"]) is not bool(want["deployment"]):
                            # We hit this section when attachment is successful, but, deployment is stuck in PENDING or
                            # OUT-OF-SYNC. In such cases, we just add the object to deploy list only. have['deployment']
                            # is set to False when deployment is PENDING or OUT-OF-SYNC - ref - get_have()
                            if bool(want["is_deploy"]):
                                dep_net = True

                        if bool(want["is_deploy"]) is not bool(have["is_deploy"]):
                            if bool(want["is_deploy"]):
                                dep_net = True

            if not found:
                if bool(want["isAttached"]):
                    del want["isAttached"]
                    want["deployment"] = True
                    attach_list.append(want)
                    if bool(want["is_deploy"]):
                        dep_net = True

        for attach in attach_list[:]:
            for ip, ser in self.ip_sn.items():
                if ser == attach["serialNumber"]:
                    ip_addr = ip
                    break
            is_vpc = self.inventory_data[ip_addr].get("isVpcConfigured")
            if is_vpc is True:
                peer_found = False
                peer_ser = self.inventory_data[ip_addr].get(
                    "peerSerialNumber"
                )
                for attch in attach_list:
                    if peer_ser == attch["serialNumber"]:
                        peer_found = True
                if not peer_found:
                    for hav in have_a:
                        if hav["serialNumber"] == peer_ser:
                            havtoattach = copy.deepcopy(hav)
                            havtoattach.update({"switchPorts": ""})
                            del havtoattach["isAttached"]
                            havtoattach["deployment"] = True
                            attach_list.append(havtoattach)
                            break

        return attach_list, dep_net

    def update_attach_params(self, attach, net_name, deploy):

        if not attach:
            return {}

        serial = ""
        attach["ip_address"] = dcnm_get_ip_addr_info(
            self.module, attach["ip_address"], None, None
        )
        for ip, ser in self.ip_sn.items():
            if ip == attach["ip_address"]:
                serial = ser

        if not serial:
            self.module.fail_json(
                msg="Fabric: {0} does not have the switch: {1}".format(
                    self.fabric, attach["ip_address"]
                )
            )

        role = self.inventory_data[attach["ip_address"]].get("switchRole")
        if role.lower() == "spine" or role.lower() == "super spine":
            msg = "Networks cannot be attached to switch {0} with role {1}".format(
                attach["ip_address"], role
            )
            self.module.fail_json(msg=msg)

        attach.update({"fabric": self.fabric})
        attach.update({"networkName": net_name})
        attach.update({"serialNumber": serial})
        attach.update({"switchPorts": ",".join(attach["ports"])})
        attach.update(
            {"detachSwitchPorts": ""}
        )  # Is this supported??Need to handle correct
        attach.update({"vlan": 0})
        attach.update({"dot1QVlan": 0})
        attach.update({"untagged": False})
        # This flag is not to be confused for deploy of attachment.
        # "deployment" should be set True for attaching an attachment
        # and set to False for detaching an attachment
        attach.update({"deployment": True})
        attach.update({"isAttached": True})
        attach.update({"extensionValues": ""})
        attach.update({"instanceValues": ""})
        attach.update({"freeformConfig": ""})
        attach.update({"is_deploy": deploy})
        if "deploy" in attach:
            del attach["deploy"]
        del attach["ports"]
        del attach["ip_address"]

        return attach

    def diff_for_create(self, want, have):

        # Possible update scenarios
        # vlanId - Changing vlanId on an already deployed network only affects new attachments
        # gwIpAddress - Changing the gwIpAddress needs all attachments to be re-deployed

        warn_msg = None
        if not have:
            return {}

        gw_changed = False
        tg_changed = False
        create = {}
        l2only_changed = False
        vn_changed = False
        intdesc_changed = False
        mtu_changed = False
        arpsup_changed = False
        dhcp1_ip_changed = False
        dhcp2_ip_changed = False
        dhcp3_ip_changed = False
        dhcp1_vrf_changed = False
        dhcp2_vrf_changed = False
        dhcp3_vrf_changed = False
        dhcp_loopback_changed = False
        multicast_group_address_changed = False
        gwv6_changed = False
        sec_gw1_changed = False
        sec_gw2_changed = False
        sec_gw3_changed = False
        sec_gw4_changed = False
        trm_en_changed = False
        rt_both_changed = False
        l3gw_onbd_changed = False
        nf_en_changed = False
        intvlan_nfmon_changed = False
        vlan_nfmon_changed = False

        if want.get("networkId") and want["networkId"] != have["networkId"]:
            self.module.fail_json(
                msg="networkId can not be updated on existing network: {0}".format(
                    want["networkName"]
                )
            )

        if have["vrf"] != want["vrf"]:
            self.module.fail_json(
                msg="The network {0} existing already can not change"
                " the VRF association from vrf:{1} to vrf:{2}".format(
                    want["networkName"], have["vrf"], want["vrf"]
                )
            )

        json_to_dict_want = json.loads(want["networkTemplateConfig"])
        json_to_dict_have = json.loads(have["networkTemplateConfig"])

        gw_ip_want = json_to_dict_want.get("gatewayIpAddress", "")
        gw_ip_have = json_to_dict_have.get("gatewayIpAddress", "")
        vlanId_want = json_to_dict_want.get("vlanId", "")
        vlanId_have = json_to_dict_have.get("vlanId")
        l2only_want = str(json_to_dict_want.get("isLayer2Only", "")).lower()
        l2only_have = json_to_dict_have.get("isLayer2Only", "")
        vlanName_want = json_to_dict_want.get("vlanName", "")
        vlanName_have = json_to_dict_have.get("vlanName", "")
        intDesc_want = json_to_dict_want.get("intfDescription", "")
        intDesc_have = json_to_dict_have.get("intfDescription", "")
        mtu_want = json_to_dict_want.get("mtu", "")
        mtu_have = json_to_dict_have.get("mtu", "")
        arpsup_want = str(json_to_dict_want.get("suppressArp", "")).lower()
        arpsup_have = json_to_dict_have.get("suppressArp", "")
        dhcp1_ip_want = json_to_dict_want.get("dhcpServerAddr1", "")
        dhcp1_ip_want = json_to_dict_want.get("dhcpServerAddr1", "")
        dhcp1_ip_have = json_to_dict_have.get("dhcpServerAddr1", "")
        dhcp2_ip_want = json_to_dict_want.get("dhcpServerAddr2", "")
        dhcp2_ip_have = json_to_dict_have.get("dhcpServerAddr2", "")
        dhcp3_ip_want = json_to_dict_want.get("dhcpServerAddr3", "")
        dhcp3_ip_have = json_to_dict_have.get("dhcpServerAddr3", "")
        dhcp1_vrf_want = json_to_dict_want.get("vrfDhcp", "")
        dhcp1_vrf_have = json_to_dict_have.get("vrfDhcp", "")
        dhcp2_vrf_want = json_to_dict_want.get("vrfDhcp2", "")
        dhcp2_vrf_have = json_to_dict_have.get("vrfDhcp2", "")
        dhcp3_vrf_want = json_to_dict_want.get("vrfDhcp3", "")
        dhcp3_vrf_have = json_to_dict_have.get("vrfDhcp3", "")
        dhcp_loopback_want = json_to_dict_want.get("loopbackId", "")
        dhcp_loopback_have = json_to_dict_have.get("loopbackId", "")
        multicast_group_address_want = json_to_dict_want.get("mcastGroup", "")
        multicast_group_address_have = json_to_dict_have.get("mcastGroup", "")
        gw_ipv6_want = json_to_dict_want.get("gatewayIpV6Address", "")
        gw_ipv6_have = json_to_dict_have.get("gatewayIpV6Address", "")
        secip_gw1_want = json_to_dict_want.get("secondaryGW1", "")
        secip_gw1_have = json_to_dict_have.get("secondaryGW1", "")
        secip_gw2_want = json_to_dict_want.get("secondaryGW2", "")
        secip_gw2_have = json_to_dict_have.get("secondaryGW2", "")
        secip_gw3_want = json_to_dict_want.get("secondaryGW3", "")
        secip_gw3_have = json_to_dict_have.get("secondaryGW3", "")
        secip_gw4_want = json_to_dict_want.get("secondaryGW4", "")
        secip_gw4_have = json_to_dict_have.get("secondaryGW4", "")
        trmen_want = str(json_to_dict_want.get("trmEnabled", "")).lower()
        trmen_have = json_to_dict_have.get("trmEnabled", "")
        rt_both_want = str(json_to_dict_want.get("rtBothAuto", "")).lower()
        rt_both_have = json_to_dict_have.get("rtBothAuto", "")
        l3gw_onbd_want = str(json_to_dict_want.get("enableL3OnBorder", "")).lower()
        l3gw_onbd_have = json_to_dict_have.get("enableL3OnBorder", "")
        nf_en_want = str(json_to_dict_want.get("ENABLE_NETFLOW", "")).lower()
        nf_en_have = json_to_dict_have.get("ENABLE_NETFLOW", "")
        intvlan_nfen_want = json_to_dict_want.get("SVI_NETFLOW_MONITOR", "")
        intvlan_nfen_have = json_to_dict_have.get("SVI_NETFLOW_MONITOR", "")
        vlan_nfen_want = json_to_dict_want.get("VLAN_NETFLOW_MONITOR", "")
        vlan_nfen_have = json_to_dict_have.get("VLAN_NETFLOW_MONITOR", "")

        if vlanId_have != "":
            vlanId_have = int(vlanId_have)
        tag_want = json_to_dict_want.get("tag", "")
        tag_have = json_to_dict_have.get("tag")
        if tag_have != "":
            tag_have = int(tag_have)
        if mtu_have != "":
            mtu_have = int(mtu_have)

        if vlanId_want:

            if (
                have["networkTemplate"] != want["networkTemplate"]
                or have["networkExtensionTemplate"] != want["networkExtensionTemplate"]
                or gw_ip_have != gw_ip_want
                or vlanId_have != vlanId_want
                or tag_have != tag_want
                or l2only_have != l2only_want
                or vlanName_have != vlanName_want
                or intDesc_have != intDesc_want
                or mtu_have != mtu_want
                or arpsup_have != arpsup_want
                or dhcp1_ip_have != dhcp1_ip_want
                or dhcp2_ip_have != dhcp2_ip_want
                or dhcp3_ip_have != dhcp3_ip_want
                or dhcp1_vrf_have != dhcp1_vrf_want
                or dhcp2_vrf_have != dhcp2_vrf_want
                or dhcp3_vrf_have != dhcp3_vrf_want
                or dhcp_loopback_have != dhcp_loopback_want
                or multicast_group_address_have != multicast_group_address_want
                or gw_ipv6_have != gw_ipv6_want
                or secip_gw1_have != secip_gw1_want
                or secip_gw2_have != secip_gw2_want
                or secip_gw3_have != secip_gw3_want
                or secip_gw4_have != secip_gw4_want
                or trmen_have != trmen_want
                or rt_both_have != rt_both_want
                or l3gw_onbd_have != l3gw_onbd_want
                or nf_en_have != nf_en_want
                or intvlan_nfen_have != intvlan_nfen_want
                or vlan_nfen_have != vlan_nfen_want
            ):
                # The network updates with missing networkId will have to use existing
                # networkId from the instance of the same network on DCNM.

                if vlanId_have != vlanId_want:
                    warn_msg = "The VLAN change will effect only new attachments."

                if gw_ip_have != gw_ip_want:
                    gw_changed = True
                if tag_have != tag_want:
                    tg_changed = True
                if l2only_have != l2only_want:
                    l2only_changed = True
                if vlanName_have != vlanName_want:
                    vn_changed = True
                if intDesc_have != intDesc_want:
                    intdesc_changed = True
                if mtu_have != mtu_want:
                    mtu_changed = True
                if arpsup_have != arpsup_want:
                    arpsup_changed = True
                if dhcp1_ip_have != dhcp1_ip_want:
                    dhcp1_ip_changed = True
                if dhcp2_ip_have != dhcp2_ip_want:
                    dhcp2_ip_changed = True
                if dhcp3_ip_have != dhcp3_ip_want:
                    dhcp3_ip_changed = True
                if dhcp1_vrf_have != dhcp1_vrf_want:
                    dhcp1_vrf_changed = True
                if dhcp2_vrf_have != dhcp2_vrf_want:
                    dhcp2_vrf_changed = True
                if dhcp3_vrf_have != dhcp3_vrf_want:
                    dhcp3_vrf_changed = True
                if dhcp_loopback_have != dhcp_loopback_want:
                    dhcp_loopback_changed = True
                if multicast_group_address_have != multicast_group_address_want:
                    multicast_group_address_changed = True
                if gw_ipv6_have != gw_ipv6_want:
                    gwv6_changed = True
                if secip_gw1_have != secip_gw1_want:
                    sec_gw1_changed = True
                if secip_gw2_have != secip_gw2_want:
                    sec_gw2_changed = True
                if secip_gw3_have != secip_gw3_want:
                    sec_gw3_changed = True
                if secip_gw4_have != secip_gw4_want:
                    sec_gw4_changed = True
                if trmen_have != trmen_want:
                    trm_en_changed = True
                if rt_both_have != rt_both_want:
                    rt_both_changed = True
                if l3gw_onbd_have != l3gw_onbd_want:
                    l3gw_onbd_changed = True
                if self.dcnm_version > 11:
                    if nf_en_have != nf_en_want:
                        nf_en_changed = True
                    if intvlan_nfen_have != intvlan_nfen_want:
                        intvlan_nfmon_changed = True
                    if vlan_nfen_have != vlan_nfen_want:
                        vlan_nfmon_changed = True

                want.update({"networkId": have["networkId"]})
                create = want

        else:

            if (
                have["networkTemplate"] != want["networkTemplate"]
                or have["networkExtensionTemplate"] != want["networkExtensionTemplate"]
                or gw_ip_have != gw_ip_want
                or tag_have != tag_want
                or l2only_have != l2only_want
                or vlanName_have != vlanName_want
                or intDesc_have != intDesc_want
                or mtu_have != mtu_want
                or arpsup_have != arpsup_want
                or dhcp1_ip_have != dhcp1_ip_want
                or dhcp2_ip_have != dhcp2_ip_want
                or dhcp3_ip_have != dhcp3_ip_want
                or dhcp1_vrf_have != dhcp1_vrf_want
                or dhcp2_vrf_have != dhcp2_vrf_want
                or dhcp3_vrf_have != dhcp3_vrf_want
                or dhcp_loopback_have != dhcp_loopback_want
                or multicast_group_address_have != multicast_group_address_want
                or gw_ipv6_have != gw_ipv6_want
                or secip_gw1_have != secip_gw1_want
                or secip_gw2_have != secip_gw2_want
                or secip_gw3_have != secip_gw3_want
                or secip_gw4_have != secip_gw4_want
                or trmen_have != trmen_want
                or rt_both_have != rt_both_want
                or l3gw_onbd_have != l3gw_onbd_want
                or nf_en_have != nf_en_want
                or intvlan_nfen_have != intvlan_nfen_want
                or vlan_nfen_have != vlan_nfen_want
            ):
                # The network updates with missing networkId will have to use existing
                # networkId from the instance of the same network on DCNM.

                if gw_ip_have != gw_ip_want:
                    gw_changed = True
                if tag_have != tag_want:
                    tg_changed = True
                if l2only_have != l2only_want:
                    l2only_changed = True
                if vlanName_have != vlanName_want:
                    vn_changed = True
                if intDesc_have != intDesc_want:
                    intdesc_changed = True
                if mtu_have != mtu_want:
                    mtu_changed = True
                if arpsup_have != arpsup_want:
                    arpsup_changed = True
                if dhcp1_ip_have != dhcp1_ip_want:
                    dhcp1_ip_changed = True
                if dhcp2_ip_have != dhcp2_ip_want:
                    dhcp2_ip_changed = True
                if dhcp3_ip_have != dhcp3_ip_want:
                    dhcp3_ip_changed = True
                if dhcp1_vrf_have != dhcp1_vrf_want:
                    dhcp1_vrf_changed = True
                if dhcp2_vrf_have != dhcp2_vrf_want:
                    dhcp2_vrf_changed = True
                if dhcp3_vrf_have != dhcp3_vrf_want:
                    dhcp3_vrf_changed = True
                if dhcp_loopback_have != dhcp_loopback_want:
                    dhcp_loopback_changed = True
                if multicast_group_address_have != multicast_group_address_want:
                    multicast_group_address_changed = True
                if gw_ipv6_have != gw_ipv6_want:
                    gwv6_changed = True
                if secip_gw1_have != secip_gw1_want:
                    sec_gw1_changed = True
                if secip_gw2_have != secip_gw2_want:
                    sec_gw2_changed = True
                if secip_gw3_have != secip_gw3_want:
                    sec_gw3_changed = True
                if secip_gw4_have != secip_gw4_want:
                    sec_gw4_changed = True
                if trmen_have != trmen_want:
                    trm_en_changed = True
                if rt_both_have != rt_both_want:
                    rt_both_changed = True
                if l3gw_onbd_have != l3gw_onbd_want:
                    l3gw_onbd_changed = True
                if self.dcnm_version > 11:
                    if nf_en_have != nf_en_want:
                        nf_en_changed = True
                    if intvlan_nfen_have != intvlan_nfen_want:
                        intvlan_nfmon_changed = True
                    if vlan_nfen_have != vlan_nfen_want:
                        vlan_nfmon_changed = True

                want.update({"networkId": have["networkId"]})
                create = want

        return (
            create,
            gw_changed,
            tg_changed,
            warn_msg,
            l2only_changed,
            vn_changed,
            intdesc_changed,
            mtu_changed,
            arpsup_changed,
            dhcp1_ip_changed,
            dhcp2_ip_changed,
            dhcp3_ip_changed,
            dhcp1_vrf_changed,
            dhcp2_vrf_changed,
            dhcp3_vrf_changed,
            dhcp_loopback_changed,
            multicast_group_address_changed,
            gwv6_changed,
            sec_gw1_changed,
            sec_gw2_changed,
            sec_gw3_changed,
            sec_gw4_changed,
            trm_en_changed,
            rt_both_changed,
            l3gw_onbd_changed,
            nf_en_changed,
            intvlan_nfmon_changed,
            vlan_nfmon_changed
        )

    def update_create_params(self, net):

        if not net:
            return net

        state = self.params["state"]

        n_template = net.get("net_template", "Default_Network_Universal")
        ne_template = net.get(
            "net_extension_template", "Default_Network_Extension_Universal"
        )

        if state == "deleted":
            net_upd = {
                "fabric": self.fabric,
                "networkName": net["net_name"],
                "networkId": net.get(
                    "net_id", None
                ),  # Network id will be auto generated in get_diff_merge()
                "networkTemplate": n_template,
                "networkExtensionTemplate": ne_template,
            }
        else:
            net_upd = {
                "fabric": self.fabric,
                "vrf": net["vrf_name"],
                "networkName": net["net_name"],
                "networkId": net.get(
                    "net_id", None
                ),  # Network id will be auto generated in get_diff_merge()
                "networkTemplate": n_template,
                "networkExtensionTemplate": ne_template,
            }

        template_conf = {
            "vlanId": net.get("vlan_id"),
            "gatewayIpAddress": net.get("gw_ip_subnet", ""),
            "isLayer2Only": net.get("is_l2only", False),
            "tag": net.get("routing_tag"),
            "vlanName": net.get("vlan_name", ""),
            "intfDescription": net.get("int_desc", ""),
            "mtu": net.get("mtu_l3intf", ""),
            "suppressArp": net.get("arp_suppress", False),
            "dhcpServerAddr1": net.get("dhcp_srvr1_ip", ""),
            "dhcpServerAddr2": net.get("dhcp_srvr2_ip", ""),
            "dhcpServerAddr3": net.get("dhcp_srvr3_ip", ""),
            "vrfDhcp": net.get("dhcp_srvr1_vrf", ""),
            "vrfDhcp2": net.get("dhcp_srvr2_vrf", ""),
            "vrfDhcp3": net.get("dhcp_srvr3_vrf", ""),
            "loopbackId": net.get("dhcp_loopback_id", ""),
            "mcastGroup": net.get("multicast_group_address", ""),
            "gatewayIpV6Address": net.get("gw_ipv6_subnet", ""),
            "secondaryGW1": net.get("secondary_ip_gw1", ""),
            "secondaryGW2": net.get("secondary_ip_gw2", ""),
            "secondaryGW3": net.get("secondary_ip_gw3", ""),
            "secondaryGW4": net.get("secondary_ip_gw4", ""),
            "trmEnabled": net.get("trm_enable", False),
            "rtBothAuto": net.get("route_target_both", False),
            "enableL3OnBorder": net.get("l3gw_on_border", False),
        }

        if self.dcnm_version > 11:
            template_conf.update(ENABLE_NETFLOW=net.get("netflow_enable", False))
            template_conf.update(SVI_NETFLOW_MONITOR=net.get("intfvlan_nf_monitor", ""))
            template_conf.update(VLAN_NETFLOW_MONITOR=net.get("vlan_nf_monitor", ""))

        if template_conf["vlanId"] is None:
            template_conf["vlanId"] = ""
        if template_conf["tag"] is None:
            template_conf["tag"] = ""
        if template_conf["vlanName"] is None:
            template_conf["vlanName"] = ""
        if template_conf["intfDescription"] is None:
            template_conf["intfDescription"] = ""
        if template_conf["mtu"] is None:
            template_conf["mtu"] = ""
        if template_conf["vrfDhcp"] is None:
            template_conf["vrfDhcp"] = ""
        if template_conf["vrfDhcp2"] is None:
            template_conf["vrfDhcp2"] = ""
        if template_conf["vrfDhcp3"] is None:
            template_conf["vrfDhcp3"] = ""
        if template_conf["loopbackId"] is None:
            template_conf["loopbackId"] = ""
        if template_conf["mcastGroup"] is None:
            template_conf["mcastGroup"] = ""
        if template_conf["gatewayIpV6Address"] is None:
            template_conf["gatewayIpV6Address"] = ""
        if template_conf["secondaryGW1"] is None:
            template_conf["secondaryGW1"] = ""
        if template_conf["secondaryGW2"] is None:
            template_conf["secondaryGW2"] = ""
        if template_conf["secondaryGW3"] is None:
            template_conf["secondaryGW3"] = ""
        if template_conf["secondaryGW4"] is None:
            template_conf["secondaryGW4"] = ""
        if self.dcnm_version > 11:
            if template_conf["SVI_NETFLOW_MONITOR"] is None:
                template_conf["SVI_NETFLOW_MONITOR"] = ""
            if template_conf["VLAN_NETFLOW_MONITOR"] is None:
                template_conf["VLAN_NETFLOW_MONITOR"] = ""

        net_upd.update({"networkTemplateConfig": json.dumps(template_conf)})

        return net_upd

    def get_have(self):

        have_create = []
        have_deploy = {}

        curr_networks = []
        dep_networks = []

        l2only_configured = False

        state = self.params["state"]

        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)

        vrf_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find VRFs under fabric: {0}".format(self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
            return

        if not state == "deleted" and not state == "query":
            if self.config:
                for net in self.config:
                    vrf_found = False
                    vrf_missing = net.get("vrf_name", "NA")
                    if (vrf_missing == "NA" or vrf_missing == "") and net.get(
                        "is_l2only", False
                    ) is True:
                        # set vrf_missing to NA again as it can be ""
                        vrf_missing = "NA"
                        vrf_found = True
                        l2only_configured = True
                        continue
                    if vrf_objects["DATA"]:
                        for vrf in vrf_objects["DATA"]:
                            if vrf_missing == vrf["vrfName"]:
                                vrf_found = True
                                break
                    if not vrf_found:
                        self.module.fail_json(
                            msg="VRF: {0} is missing in fabric: {1}".format(
                                vrf_missing, self.fabric
                            )
                        )

        for vrf in vrf_objects["DATA"]:

            path = self.paths["GET_VRF_NET"].format(self.fabric, vrf["vrfName"])

            networks_per_vrf = dcnm_send(self.module, method, path)

            if not networks_per_vrf["DATA"]:
                continue

            for net in networks_per_vrf["DATA"]:
                json_to_dict = json.loads(net["networkTemplateConfig"])
                t_conf = {
                    "vlanId": json_to_dict.get("vlanId", ""),
                    "gatewayIpAddress": json_to_dict.get("gatewayIpAddress", ""),
                    "isLayer2Only": json_to_dict.get("isLayer2Only", False),
                    "tag": json_to_dict.get("tag", ""),
                    "vlanName": json_to_dict.get("vlanName", ""),
                    "intfDescription": json_to_dict.get("intfDescription", ""),
                    "mtu": json_to_dict.get("mtu", ""),
                    "suppressArp": json_to_dict.get("suppressArp", False),
                    "dhcpServerAddr1": json_to_dict.get("dhcpServerAddr1", ""),
                    "dhcpServerAddr2": json_to_dict.get("dhcpServerAddr2", ""),
                    "dhcpServerAddr3": json_to_dict.get("dhcpServerAddr3", ""),
                    "vrfDhcp": json_to_dict.get("vrfDhcp", ""),
                    "vrfDhcp2": json_to_dict.get("vrfDhcp2", ""),
                    "vrfDhcp3": json_to_dict.get("vrfDhcp3", ""),
                    "loopbackId": json_to_dict.get("loopbackId", ""),
                    "mcastGroup": json_to_dict.get("mcastGroup", ""),
                    "gatewayIpV6Address": json_to_dict.get("gatewayIpV6Address", ""),
                    "secondaryGW1": json_to_dict.get("secondaryGW1", ""),
                    "secondaryGW2": json_to_dict.get("secondaryGW2", ""),
                    "secondaryGW3": json_to_dict.get("secondaryGW3", ""),
                    "secondaryGW4": json_to_dict.get("secondaryGW4", ""),
                    "trmEnabled": json_to_dict.get("trmEnabled", False),
                    "rtBothAuto": json_to_dict.get("rtBothAuto", False),
                    "enableL3OnBorder": json_to_dict.get("enableL3OnBorder", False),
                }

                if self.dcnm_version > 11:
                    t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW", False))
                    t_conf.update(SVI_NETFLOW_MONITOR=json_to_dict.get("SVI_NETFLOW_MONITOR", ""))
                    t_conf.update(VLAN_NETFLOW_MONITOR=json_to_dict.get("VLAN_NETFLOW_MONITOR", ""))

                net.update({"networkTemplateConfig": json.dumps(t_conf)})
                del net["displayName"]
                del net["serviceNetworkTemplate"]
                del net["source"]

                curr_networks.append(net["networkName"])

                have_create.append(net)

        if l2only_configured is True or state == "deleted":
            path = self.paths["GET_VRF_NET"].format(self.fabric, "NA")
            networks_per_navrf = dcnm_send(self.module, method, path)

            if networks_per_navrf.get("DATA"):
                for l2net in networks_per_navrf["DATA"]:
                    json_to_dict = json.loads(l2net["networkTemplateConfig"])
                    if (json_to_dict.get("vrfName", "")) == "NA":
                        t_conf = {
                            "vlanId": json_to_dict.get("vlanId", ""),
                            "gatewayIpAddress": json_to_dict.get("gatewayIpAddress", ""),
                            "isLayer2Only": json_to_dict.get("isLayer2Only", False),
                            "tag": json_to_dict.get("tag", ""),
                            "vlanName": json_to_dict.get("vlanName", ""),
                            "intfDescription": json_to_dict.get("intfDescription", ""),
                            "mtu": json_to_dict.get("mtu", ""),
                            "suppressArp": json_to_dict.get("suppressArp", False),
                            "dhcpServerAddr1": json_to_dict.get("dhcpServerAddr1", ""),
                            "dhcpServerAddr2": json_to_dict.get("dhcpServerAddr2", ""),
                            "dhcpServerAddr3": json_to_dict.get("dhcpServerAddr3", ""),
                            "vrfDhcp": json_to_dict.get("vrfDhcp", ""),
                            "vrfDhcp2": json_to_dict.get("vrfDhcp2", ""),
                            "vrfDhcp3": json_to_dict.get("vrfDhcp3", ""),
                            "loopbackId": json_to_dict.get("loopbackId", ""),
                            "mcastGroup": json_to_dict.get("mcastGroup", ""),
                            "gatewayIpV6Address": json_to_dict.get("gatewayIpV6Address", ""),
                            "secondaryGW1": json_to_dict.get("secondaryGW1", ""),
                            "secondaryGW2": json_to_dict.get("secondaryGW2", ""),
                            "secondaryGW3": json_to_dict.get("secondaryGW3", ""),
                            "secondaryGW4": json_to_dict.get("secondaryGW4", ""),
                            "trmEnabled": json_to_dict.get("trmEnabled", False),
                            "rtBothAuto": json_to_dict.get("rtBothAuto", False),
                            "enableL3OnBorder": json_to_dict.get("enableL3OnBorder", False),
                        }

                        if self.dcnm_version > 11:
                            t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW", False))
                            t_conf.update(SVI_NETFLOW_MONITOR=json_to_dict.get("SVI_NETFLOW_MONITOR", ""))
                            t_conf.update(VLAN_NETFLOW_MONITOR=json_to_dict.get("VLAN_NETFLOW_MONITOR", ""))

                        l2net.update({"networkTemplateConfig": json.dumps(t_conf)})
                        del l2net["displayName"]
                        del l2net["serviceNetworkTemplate"]
                        del l2net["source"]

                        curr_networks.append(l2net["networkName"])

                        have_create.append(l2net)

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
            dep_net = ""
            for attach in attach_list:
                attach_state = False if attach["lanAttachState"] == "NA" else True
                deploy = attach["isLanAttached"]
                deployed = False
                if bool(deploy) and (
                    attach["lanAttachState"] == "OUT-OF-SYNC"
                    or attach["lanAttachState"] == "PENDING"
                ):
                    deployed = False
                else:
                    deployed = True

                if bool(deployed):
                    dep_net = attach["networkName"]

                sn = attach["switchSerialNo"]
                vlan = attach["vlanId"]
                ports = attach["portNames"]

                # The deletes and updates below are done to update the incoming dictionary format to
                # match to what the outgoing payload requirements mandate.
                # Ex: 'vlanId' in the attach section of incoming payload needs to be changed to 'vlan'
                # on the attach section of outgoing payload.

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

                if "displayName" in attach.keys():
                    del attach["displayName"]
                if "interfaceGroups" in attach.keys():
                    del attach["interfaceGroups"]

                attach.update({"fabric": self.fabric})
                attach.update({"vlan": vlan})
                attach.update({"serialNumber": sn})
                attach.update({"deployment": deploy})
                attach.update({"extensionValues": ""})
                attach.update({"instanceValues": ""})
                attach.update({"freeformConfig": ""})
                attach.update({"isAttached": attach_state})
                attach.update({"dot1QVlan": 0})
                attach.update({"detachSwitchPorts": ""})
                attach.update({"switchPorts": ports})
                attach.update({"untagged": False})
                attach.update({"is_deploy": deployed})

            if dep_net:
                dep_networks.append(dep_net)

        have_attach = net_attach_objects["DATA"]

        if dep_networks:
            have_deploy.update({"networkNames": ",".join(dep_networks)})

        self.have_create = have_create
        self.have_attach = have_attach
        self.have_deploy = have_deploy

    def get_want(self):

        want_create = []
        want_attach = []
        want_deploy = {}

        all_networks = ""

        if not self.config:
            return

        for net in self.validated:
            net_attach = {}
            networks = []

            net_deploy = net.get("deploy", True)

            want_create.append(self.update_create_params(net))

            if not net.get("attach"):
                continue
            for attach in net["attach"]:
                deploy = net_deploy
                networks.append(
                    self.update_attach_params(attach, net["net_name"], deploy)
                )
            if networks:
                for attch in net["attach"]:
                    for ip, ser in self.ip_sn.items():
                        if ser == attch["serialNumber"]:
                            ip_address = ip
                            break
                    # deploy = attch["deployment"]
                    is_vpc = self.inventory_data[ip_address].get(
                        "isVpcConfigured"
                    )
                    if is_vpc is True:
                        peer_found = False
                        peer_ser = self.inventory_data[ip_address].get(
                            "peerSerialNumber"
                        )
                        for network in networks:
                            if peer_ser == network["serialNumber"]:
                                peer_found = True
                                break
                        if not peer_found:
                            msg = (
                                "Switch {0} in fabric {1} is configured for vPC, "
                                "please attach the peer switch also to network"
                                .format(ip_address, self.fabric))
                            self.module.fail_json(msg=msg)
                            # This code add the peer switch in vpc cases automatically
                            # As of now UI return error in such cases. Uncomment this if
                            # UI behaviour changes
                            # attach_dict = dict(ip_address="", ports=[], deploy=True)
                            # for ip, ser in self.ip_sn.items():
                            #     if ser == peer_ser:
                            #         ip_addr = ip
                            #         break
                            # attach_dict.update({"ip_address": ip_addr})
                            # networks.append(
                            #     self.update_attach_params(
                            #         attach_dict, net["net_name"], deploy
                            #     )
                            # )
                net_attach.update({"networkName": net["net_name"]})
                net_attach.update({"lanAttachList": networks})
                want_attach.append(net_attach)

            all_networks += net["net_name"] + ","

        if all_networks:
            want_deploy.update({"networkNames": all_networks[:-1]})

        self.want_create = want_create
        self.want_attach = want_attach
        self.want_deploy = want_deploy

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
                    if a_h["isAttached"]:
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        to_del.append(a_h)
                if to_del:
                    have_a.update({"lanAttachList": to_del})
                    diff_detach.append(have_a)
                    all_nets += have_a["networkName"] + ","
            if all_nets:
                diff_undeploy.update({"networkNames": all_nets[:-1]})

        else:
            for have_a in self.have_attach:
                to_del = []
                atch_h = have_a["lanAttachList"]
                for a_h in atch_h:
                    if a_h["isAttached"]:
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        to_del.append(a_h)
                if to_del:
                    have_a.update({"lanAttachList": to_del})
                    diff_detach.append(have_a)
                    all_nets += have_a["networkName"] + ","

                diff_delete.update({have_a["networkName"]: "DEPLOYED"})
            if all_nets:
                diff_undeploy.update({"networkNames": all_nets[:-1]})

        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

    def get_diff_override(self):

        all_nets = ""
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
                    if a_h["isAttached"]:
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        to_del.append(a_h)

                if to_del:
                    have_a.update({"lanAttachList": to_del})
                    diff_detach.append(have_a)
                    all_nets += have_a["networkName"] + ","

                # The following is added just to help in deletion, we need to wait for detach transaction to complete
                # before attempting to delete the network.
                diff_delete.update({have_a["networkName"]: "DEPLOYED"})

        if all_nets:
            diff_undeploy.update({"networkNames": all_nets[:-1]})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete
        self.diff_detach = diff_detach
        return warn_msg

    def get_diff_replace(self):

        all_nets = ""

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
                        if not a_h["isAttached"]:
                            continue
                        a_match = False

                        if atch_w:
                            for a_w in atch_w:
                                if a_h["serialNumber"] == a_w["serialNumber"]:
                                    # Have is already in diff, no need to continue looking for it.
                                    a_match = True
                                    break
                        if not a_match:
                            del a_h["isAttached"]
                            a_h.update({"deployment": False})
                            r_net_list.append(a_h)
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
                        if not a_h["isAttached"]:
                            continue
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        r_net_list.append(a_h)

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
                    all_nets += have_a["networkName"] + ","

        if not all_nets:
            self.diff_create = diff_create
            self.diff_attach = diff_attach
            self.diff_deploy = diff_deploy
            return warn_msg

        if not self.diff_deploy:
            diff_deploy.update({"networkNames": all_nets[:-1]})
        else:
            nets = self.diff_deploy["networkNames"] + "," + all_nets[:-1]
            diff_deploy.update({"networkNames": nets})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        return warn_msg

    def get_diff_merge(self, replace=False):

        #
        # Special cases:
        # 1. Update gateway on an existing network:
        #    We need to use the network_update API with PUT method to update the nw with new gw.
        #    attach logic remains same, but, we need to re-deploy the network in any case to reflect the new gw.
        # 2. Update vlan-id on an existing network:
        #    This change will only affect new attachments of the same network.
        # 3. Auto generate networkId if its not mentioned by user:
        #    In this case, we need to query the DCNM to get a usable ID and use it in the payload.
        #    And also, any such network create requests need to be pushed individually(not bulk op).

        diff_create = []
        diff_create_update = []
        diff_create_quick = []
        diff_attach = []
        diff_deploy = {}
        prev_net_id_fetched = None

        gw_changed = {}
        tg_changed = {}
        warn_msg = None
        l2only_changed = {}
        vn_changed = {}
        intdesc_changed = {}
        mtu_changed = {}
        arpsup_changed = {}
        dhcp1_ip_changed = {}
        dhcp2_ip_changed = {}
        dhcp3_ip_changed = {}
        dhcp1_vrf_changed = {}
        dhcp2_vrf_changed = {}
        dhcp3_vrf_changed = {}
        dhcp_loopback_changed = {}
        multicast_group_address_changed = {}
        gwv6_changed = {}
        sec_gw1_changed = {}
        sec_gw2_changed = {}
        sec_gw3_changed = {}
        sec_gw4_changed = {}
        trm_en_changed = {}
        rt_both_changed = {}
        l3gw_onbd_changed = {}
        nf_en_changed = {}
        intvlan_nfmon_changed = {}
        vlan_nfmon_changed = {}

        for want_c in self.want_create:
            found = False
            for have_c in self.have_create:
                if want_c["networkName"] == have_c["networkName"]:

                    found = True
                    (
                        diff,
                        gw_chg,
                        tg_chg,
                        warn_msg,
                        l2only_chg,
                        vn_chg,
                        idesc_chg,
                        mtu_chg,
                        arpsup_chg,
                        dhcp1_ip_chg,
                        dhcp2_ip_chg,
                        dhcp3_ip_chg,
                        dhcp1_vrf_chg,
                        dhcp2_vrf_chg,
                        dhcp3_vrf_chg,
                        dhcp_loopbk_chg,
                        mcast_grp_chg,
                        gwv6_chg,
                        sec_gw1_chg,
                        sec_gw2_chg,
                        sec_gw3_chg,
                        sec_gw4_chg,
                        trm_en_chg,
                        rt_both_chg,
                        l3gw_onbd_chg,
                        nf_en_chg,
                        intvlan_nfmon_chg,
                        vlan_nfmon_chg
                    ) = self.diff_for_create(want_c, have_c)
                    gw_changed.update({want_c["networkName"]: gw_chg})
                    tg_changed.update({want_c["networkName"]: tg_chg})
                    l2only_changed.update({want_c["networkName"]: l2only_chg})
                    vn_changed.update({want_c["networkName"]: vn_chg})
                    intdesc_changed.update({want_c["networkName"]: idesc_chg})
                    mtu_changed.update({want_c["networkName"]: mtu_chg})
                    arpsup_changed.update({want_c["networkName"]: arpsup_chg})
                    dhcp1_ip_changed.update({want_c["networkName"]: dhcp1_ip_chg})
                    dhcp2_ip_changed.update({want_c["networkName"]: dhcp2_ip_chg})
                    dhcp3_ip_changed.update({want_c["networkName"]: dhcp3_ip_chg})
                    dhcp1_vrf_changed.update({want_c["networkName"]: dhcp1_vrf_chg})
                    dhcp2_vrf_changed.update({want_c["networkName"]: dhcp2_vrf_chg})
                    dhcp3_vrf_changed.update({want_c["networkName"]: dhcp3_vrf_chg})
                    dhcp_loopback_changed.update(
                        {want_c["networkName"]: dhcp_loopbk_chg}
                    )
                    multicast_group_address_changed.update(
                        {want_c["networkName"]: mcast_grp_chg}
                    )
                    gwv6_changed.update({want_c["networkName"]: gwv6_chg})
                    sec_gw1_changed.update({want_c["networkName"]: sec_gw1_chg})
                    sec_gw2_changed.update({want_c["networkName"]: sec_gw2_chg})
                    sec_gw3_changed.update({want_c["networkName"]: sec_gw3_chg})
                    sec_gw4_changed.update({want_c["networkName"]: sec_gw4_chg})
                    trm_en_changed.update({want_c["networkName"]: trm_en_chg})
                    rt_both_changed.update({want_c["networkName"]: rt_both_chg})
                    l3gw_onbd_changed.update({want_c["networkName"]: l3gw_onbd_chg})
                    nf_en_changed.update({want_c["networkName"]: nf_en_chg})
                    intvlan_nfmon_changed.update({want_c["networkName"]: intvlan_nfmon_chg})
                    vlan_nfmon_changed.update({want_c["networkName"]: vlan_nfmon_chg})
                    if diff:
                        diff_create_update.append(diff)
                    break
            if not found:
                net_id = want_c.get("networkId", None)

                if not net_id:
                    # networkId(VNI-id) is not provided by user.
                    # Need to query DCNM to fetch next available networkId and use it here.

                    method = "POST"

                    attempt = 0
                    while attempt < 10:
                        attempt += 1
                        path = self.paths["GET_NET_ID"].format(self.fabric)
                        if self.dcnm_version > 11:
                            net_id_obj = dcnm_send(self.module, "GET", path)
                        else:
                            net_id_obj = dcnm_send(self.module, method, path)

                        missing_fabric, not_ok = self.handle_response(
                            net_id_obj, "query_dcnm"
                        )

                        if missing_fabric or not_ok:
                            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                            msg2 = (
                                "Unable to generate networkId for network: {0} "
                                "under fabric: {1}".format(
                                    want_c["networkName"], self.fabric
                                )
                            )

                            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

                        if not net_id_obj["DATA"]:
                            continue

                        if self.dcnm_version == 11:
                            net_id = net_id_obj["DATA"].get("segmentId")
                        elif self.dcnm_version >= 12:
                            net_id = net_id_obj["DATA"].get("l2vni")
                        else:
                            msg = "Unsupported DCNM version: version {0}".format(
                                self.dcnm_version
                            )
                            self.module.fail_json(msg)

                        if net_id != prev_net_id_fetched:
                            want_c.update({"networkId": net_id})
                            prev_net_id_fetched = net_id
                            break

                    if not net_id:
                        self.module.fail_json(
                            msg="Unable to generate networkId for network: {0} "
                            "under fabric: {1}".format(
                                want_c["networkName"], self.fabric
                            )
                        )

                    create_path = self.paths["GET_NET"].format(self.fabric)
                    diff_create_quick.append(want_c)

                    if self.module.check_mode:
                        continue

                    resp = dcnm_send(
                        self.module, method, create_path, json.dumps(want_c)
                    )
                    self.result["response"].append(resp)
                    fail, self.result["changed"] = self.handle_response(resp, "create")
                    if fail:
                        self.failure(resp)

                else:
                    diff_create.append(want_c)

        all_nets = []
        for want_a in self.want_attach:
            dep_net = ""
            found = False
            for have_a in self.have_attach:
                if want_a["networkName"] == have_a["networkName"]:

                    found = True
                    diff, net = self.diff_for_attach_deploy(
                        want_a["lanAttachList"], have_a["lanAttachList"], replace
                    )

                    if diff:
                        base = want_a.copy()
                        del base["lanAttachList"]
                        base.update({"lanAttachList": diff})
                        diff_attach.append(base)
                        if net:
                            dep_net = want_a["networkName"]
                    else:
                        if (
                            net
                            or gw_changed.get(want_a["networkName"], False)
                            or tg_changed.get(want_a["networkName"], False)
                            or l2only_changed.get(want_a["networkName"], False)
                            or vn_changed.get(want_a["networkName"], False)
                            or intdesc_changed.get(want_a["networkName"], False)
                            or mtu_changed.get(want_a["networkName"], False)
                            or arpsup_changed.get(want_a["networkName"], False)
                            or dhcp1_ip_changed.get(want_a["networkName"], False)
                            or dhcp2_ip_changed.get(want_a["networkName"], False)
                            or dhcp3_ip_changed.get(want_a["networkName"], False)
                            or dhcp1_vrf_changed.get(want_a["networkName"], False)
                            or dhcp2_vrf_changed.get(want_a["networkName"], False)
                            or dhcp3_vrf_changed.get(want_a["networkName"], False)
                            or dhcp_loopback_changed.get(want_a["networkName"], False)
                            or multicast_group_address_changed.get(want_a["networkName"], False)
                            or gwv6_changed.get(want_a["networkName"], False)
                            or sec_gw1_changed.get(want_a["networkName"], False)
                            or sec_gw2_changed.get(want_a["networkName"], False)
                            or sec_gw3_changed.get(want_a["networkName"], False)
                            or sec_gw4_changed.get(want_a["networkName"], False)
                            or trm_en_changed.get(want_a["networkName"], False)
                            or rt_both_changed.get(want_a["networkName"], False)
                            or l3gw_onbd_changed.get(want_a["networkName"], False)
                            or nf_en_changed.get(want_a["networkName"], False)
                            or intvlan_nfmon_changed.get(want_a["networkName"], False)
                            or vlan_nfmon_changed.get(want_a["networkName"], False)
                        ):
                            dep_net = want_a["networkName"]

            if not found and want_a.get("lanAttachList"):
                atch_list = []
                for attach in want_a["lanAttachList"]:
                    # Saftey check
                    if attach.get("isAttached"):
                        del attach["isAttached"]
                        atch_list.append(attach)
                if atch_list:
                    base = want_a.copy()
                    del base["lanAttachList"]
                    base.update({"lanAttachList": atch_list})
                    diff_attach.append(base)
                    if bool(attach["is_deploy"]):
                        dep_net = want_a["networkName"]

                for atch in atch_list:
                    atch["deployment"] = True

            if dep_net:
                all_nets.append(dep_net)

        if all_nets:
            diff_deploy.update({"networkNames": ",".join(all_nets)})

        self.diff_create = diff_create
        self.diff_create_update = diff_create_update
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_create_quick = diff_create_quick

        return warn_msg

    def format_diff(self):

        diff = []

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_quick = copy.deepcopy(self.diff_create_quick)
        diff_create_update = copy.deepcopy(self.diff_create_update)
        diff_attach = copy.deepcopy(self.diff_attach)
        diff_detach = copy.deepcopy(self.diff_detach)
        diff_deploy = (
            self.diff_deploy["networkNames"].split(",") if self.diff_deploy else []
        )
        diff_undeploy = (
            self.diff_undeploy["networkNames"].split(",") if self.diff_undeploy else []
        )

        diff_create.extend(diff_create_quick)
        diff_create.extend(diff_create_update)
        diff_attach.extend(diff_detach)
        diff_deploy.extend(diff_undeploy)

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

            json_to_dict = json.loads(found_c["networkTemplateConfig"])

            found_c.update({"net_name": found_c["networkName"]})
            found_c.update({"vrf_name": found_c.get("vrf", "NA")})
            found_c.update({"net_id": found_c["networkId"]})
            found_c.update({"vlan_id": json_to_dict.get("vlanId", "")})
            found_c.update({"gw_ip_subnet": json_to_dict.get("gatewayIpAddress", "")})
            found_c.update({"net_template": found_c["networkTemplate"]})
            found_c.update(
                {"net_extension_template": found_c["networkExtensionTemplate"]}
            )
            found_c.update({"is_l2only": json_to_dict.get("isLayer2Only", False)})
            found_c.update({"vlan_name": json_to_dict.get("vlanName", "")})
            found_c.update({"int_desc": json_to_dict.get("intfDescription", "")})
            found_c.update({"mtu_l3intf": json_to_dict.get("mtu", "")})
            found_c.update({"arp_suppress": json_to_dict.get("suppressArp", False)})
            found_c.update({"dhcp_srvr1_ip": json_to_dict.get("dhcpServerAddr1", "")})
            found_c.update({"dhcp_srvr2_ip": json_to_dict.get("dhcpServerAddr2", "")})
            found_c.update({"dhcp_srvr3_ip": json_to_dict.get("dhcpServerAddr3", "")})
            found_c.update({"dhcp_srvr1_vrf": json_to_dict.get("vrfDhcp", "")})
            found_c.update({"dhcp_srvr2_vrf": json_to_dict.get("vrfDhcp2", "")})
            found_c.update({"dhcp_srvr3_vrf": json_to_dict.get("vrfDhcp3", "")})
            found_c.update({"dhcp_loopback_id": json_to_dict.get("loopbackId", "")})
            found_c.update({"multicast_group_address": json_to_dict.get("mcastGroup", "")})
            found_c.update({"gw_ipv6_subnet": json_to_dict.get("gatewayIpV6Address", "")})
            found_c.update({"secondary_ip_gw1": json_to_dict.get("secondaryGW1", "")})
            found_c.update({"secondary_ip_gw2": json_to_dict.get("secondaryGW2", "")})
            found_c.update({"secondary_ip_gw3": json_to_dict.get("secondaryGW3", "")})
            found_c.update({"secondary_ip_gw4": json_to_dict.get("secondaryGW4", "")})
            found_c.update({"trm_enable": json_to_dict.get("trmEnabled", False)})
            found_c.update({"route_target_both": json_to_dict.get("rtBothAuto", False)})
            found_c.update({"l3gw_on_border": json_to_dict.get("enableL3OnBorder", False)})
            if self.dcnm_version > 11:
                found_c.update({"netflow_enable": json_to_dict.get("ENABLE_NETFLOW", False)})
                found_c.update({"intfvlan_nf_monitor": json_to_dict.get("SVI_NETFLOW_MONITOR", "")})
                found_c.update({"vlan_nf_monitor": json_to_dict.get("VLAN_NETFLOW_MONITOR", "")})
            found_c.update({"attach": []})

            del found_c["fabric"]
            del found_c["networkName"]
            del found_c["networkId"]
            del found_c["networkTemplate"]
            del found_c["networkExtensionTemplate"]
            del found_c["networkTemplateConfig"]
            del found_c["vrf"]

            if diff_deploy and found_c["net_name"] in diff_deploy:
                diff_deploy.remove(found_c["net_name"])
            if not found_a:
                diff.append(found_c)
                continue

            attach = found_a["lanAttachList"]

            for a_w in attach:
                attach_d = {}
                detach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w["serialNumber"]:
                        attach_d.update({"ip_address": k})
                        break
                if a_w["detachSwitchPorts"]:
                    detach_d.update({"ip_address": attach_d["ip_address"]})
                    detach_d.update({"ports": a_w["detachSwitchPorts"]})
                    detach_d.update({"deploy": False})
                    found_c["attach"].append(detach_d)
                attach_d.update({"ports": a_w["switchPorts"]})
                attach_d.update({"deploy": a_w["deployment"]})
                found_c["attach"].append(attach_d)

            diff.append(found_c)

            diff_attach.remove(found_a)

        for vrf in diff_attach:
            new_attach_dict = {}
            new_attach_list = []
            attach = vrf["lanAttachList"]

            for a_w in attach:
                attach_d = {}
                detach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w["serialNumber"]:
                        attach_d.update({"ip_address": k})
                        break
                if a_w["detachSwitchPorts"]:
                    detach_d.update({"ip_address": attach_d["ip_address"]})
                    detach_d.update({"ports": a_w["detachSwitchPorts"]})
                    detach_d.update({"deploy": False})
                    new_attach_list.append(detach_d)
                attach_d.update({"ports": a_w["switchPorts"]})
                attach_d.update({"deploy": a_w["deployment"]})
                new_attach_list.append(attach_d)

            if new_attach_list:
                if diff_deploy and vrf["networkName"] in diff_deploy:
                    diff_deploy.remove(vrf["networkName"])
                new_attach_dict.update({"attach": new_attach_list})
                new_attach_dict.update({"net_name": vrf["networkName"]})
                diff.append(new_attach_dict)

        for net in diff_deploy:
            new_deploy_dict = {"net_name": net}
            diff.append(new_deploy_dict)

        self.diff_input_format = diff

    def get_diff_query(self):

        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)

        vrf_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find VRFs under fabric: {0}".format(self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
            return

        if self.config:
            query = []
            if self.have_create or self.have_attach:
                for want_c in self.want_create:
                    # Query the Network
                    item = {"parent": {}, "attach": []}
                    path = self.paths["GET_NET_NAME"].format(
                        self.fabric, want_c["networkName"]
                    )
                    network = dcnm_send(self.module, method, path)

                    if not network["DATA"]:
                        continue

                    net = network["DATA"]
                    if want_c["networkName"] == net["networkName"]:
                        item["parent"] = net
                        item["parent"]["networkTemplateConfig"] = json.loads(
                            net["networkTemplateConfig"]
                        )

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
                item = {"parent": {}, "attach": []}
                # append the parent network details
                item["parent"] = net
                item["parent"]["networkTemplateConfig"] = json.loads(
                    net["networkTemplateConfig"]
                )

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

    def wait_for_del_ready(self):

        method = "GET"
        if self.diff_delete:
            for net in self.diff_delete:
                state = False
                path = self.paths["GET_NET_ATTACH"].format(self.fabric, net)
                while not state:
                    resp = dcnm_send(self.module, method, path)
                    state = True
                    if resp["DATA"]:
                        attach_list = resp["DATA"][0]["lanAttachList"]
                        for atch in attach_list:
                            if (
                                atch["lanAttachState"] == "OUT-OF-SYNC"
                                or atch["lanAttachState"] == "FAILED"
                            ):
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

    def push_to_remote(self, is_rollback=False):

        path = self.paths["GET_NET"].format(self.fabric)

        method = "PUT"
        if self.diff_create_update:
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

        #
        # The detach and un-deploy operations are executed before the create,attach and deploy to particularly
        # address cases where a VLAN of a network being deleted is re-used on a new network being created. This is
        # needed specially for state: overridden
        #

        method = "POST"
        if self.diff_detach:
            detach_path = path + "/attachments"

            # Update the fabric name to specific fabric which the switches are part of.
            self.update_ms_fabric(self.diff_detach)

            for d_a in self.diff_detach:
                for v_a in d_a["lanAttachList"]:
                    del v_a["is_deploy"]

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

        method = "POST"
        if self.diff_undeploy:
            deploy_path = path + "/deployments"
            resp = dcnm_send(
                self.module, method, deploy_path, json.dumps(self.diff_undeploy)
            )
            # Use the self.wait_for_del_ready() function to refresh the state
            # of self.diff_delete dict and re-attempt the undeploy action if
            # the state of the network is "OUT-OF-SYNC"
            self.wait_for_del_ready()
            for net, state in self.diff_delete.items():
                if state == "OUT-OF-SYNC":
                    resp = dcnm_send(
                        self.module, method, deploy_path, json.dumps(self.diff_undeploy)
                    )

            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "deploy")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        method = "DELETE"
        del_failure = ""
        if self.diff_delete and self.wait_for_del_ready():
            for net, state in self.diff_delete.items():
                if state == "OUT-OF-SYNC":
                    del_failure += net + ","
                    continue
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

        if self.diff_create:
            for net in self.diff_create:
                json_to_dict = json.loads(net["networkTemplateConfig"])
                vlanId = json_to_dict.get("vlanId", "")

                if not vlanId:
                    vlan_path = self.paths["GET_VLAN"].format(self.fabric)
                    vlan_data = dcnm_send(self.module, "GET", vlan_path)

                    if vlan_data["RETURN_CODE"] != 200:
                        self.module.fail_json(
                            msg="Failure getting autogenerated vlan_id {0}".format(
                                vlan_data
                            )
                        )
                    vlanId = vlan_data["DATA"]

                t_conf = {
                    "vlanId": vlanId,
                    "gatewayIpAddress": json_to_dict.get("gatewayIpAddress", ""),
                    "isLayer2Only": json_to_dict.get("isLayer2Only", False),
                    "tag": json_to_dict.get("tag", ""),
                    "vlanName": json_to_dict.get("vlanName", ""),
                    "intfDescription": json_to_dict.get("intfDescription", ""),
                    "mtu": json_to_dict.get("mtu", ""),
                    "suppressArp": json_to_dict.get("suppressArp", False),
                    "dhcpServerAddr1": json_to_dict.get("dhcpServerAddr1", ""),
                    "dhcpServerAddr2": json_to_dict.get("dhcpServerAddr2", ""),
                    "dhcpServerAddr3": json_to_dict.get("dhcpServerAddr3", ""),
                    "vrfDhcp": json_to_dict.get("vrfDhcp", ""),
                    "vrfDhcp2": json_to_dict.get("vrfDhcp2", ""),
                    "vrfDhcp3": json_to_dict.get("vrfDhcp3", ""),
                    "loopbackId": json_to_dict.get("loopbackId", ""),
                    "mcastGroup": json_to_dict.get("mcastGroup", ""),
                    "gatewayIpV6Address": json_to_dict.get("gatewayIpV6Address", ""),
                    "secondaryGW1": json_to_dict.get("secondaryGW1", ""),
                    "secondaryGW2": json_to_dict.get("secondaryGW2", ""),
                    "secondaryGW3": json_to_dict.get("secondaryGW3", ""),
                    "secondaryGW4": json_to_dict.get("secondaryGW4", ""),
                    "trmEnabled": json_to_dict.get("trmEnabled", False),
                    "rtBothAuto": json_to_dict.get("rtBothAuto", False),
                    "enableL3OnBorder": json_to_dict.get("enableL3OnBorder", False),
                }

                if self.dcnm_version > 11:
                    t_conf.update(ENABLE_NETFLOW=json_to_dict.get("ENABLE_NETFLOW", False))
                    t_conf.update(SVI_NETFLOW_MONITOR=json_to_dict.get("SVI_NETFLOW_MONITOR", ""))
                    t_conf.update(VLAN_NETFLOW_MONITOR=json_to_dict.get("VLAN_NETFLOW_MONITOR", ""))

                net.update({"networkTemplateConfig": json.dumps(t_conf)})

                method = "POST"
                resp = dcnm_send(self.module, method, path, json.dumps(net))
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "create")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        method = "POST"
        if self.diff_attach:
            attach_path = path + "/attachments"

            # Update the fabric name to specific fabric which the switches are part of.
            self.update_ms_fabric(self.diff_attach)

            for d_a in self.diff_attach:
                for v_a in d_a["lanAttachList"]:
                    del v_a["is_deploy"]

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

        method = "POST"
        if self.diff_deploy:
            deploy_path = path + "/deployments"
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

    def validate_input(self):
        """Parse the playbook values, validate to param specs."""

        state = self.params["state"]

        if state == "query":

            # If ingress replication is enabled multicast group address should be set to "" as default.
            # If ingress replication is not enabled, the default value for multicast group address
            # is different for DCNM and NDFC.
            if self.fabric_det.get("replicationMode") == "Ingress":
                mcast_group_addr = ""
            elif self.dcnm_version > 11:
                mcast_group_addr = "239.1.1.1"
            else:
                mcast_group_addr = "239.1.1.0"

            net_spec = dict(
                net_name=dict(required=True, type="str", length_max=64),
                net_id=dict(type="int", range_max=16777214),
                vrf_name=dict(type="str", length_max=32),
                attach=dict(type="list"),
                deploy=dict(type="bool"),
                gw_ip_subnet=dict(type="ipv4_subnet", default=""),
                vlan_id=dict(type="int", range_max=4094),
                routing_tag=dict(type="int", default=12345, range_max=4294967295),
                net_template=dict(type="str", default="Default_Network_Universal"),
                net_extension_template=dict(
                    type="str", default="Default_Network_Extension_Universal"
                ),
                is_l2only=dict(type="bool", default=False),
                vlan_name=dict(type="str", length_max=128),
                int_desc=dict(type="str", length_max=258),
                mtu_l3intf=dict(type="int", range_min=68, range_max=9216),
                arp_suppress=dict(type="bool", default=False),
                dhcp_srvr1_ip=dict(type="ipv4", default=""),
                dhcp_srvr2_ip=dict(type="ipv4", default=""),
                dhcp_srvr3_ip=dict(type="ipv4", default=""),
                dhcp_srvr1_vrf=dict(type="str", length_max=32),
                dhcp_srvr2_vrf=dict(type="str", length_max=32),
                dhcp_srvr3_vrf=dict(type="str", length_max=32),
                dhcp_loopback_id=dict(type="int", range_min=0, range_max=1023),
                multicast_group_address=dict(type="ipv4", default=mcast_group_addr),
                gw_ipv6_subnet=dict(type="ipv6_subnet", default=""),
                secondary_ip_gw1=dict(type="ipv4", default=""),
                secondary_ip_gw2=dict(type="ipv4", default=""),
                secondary_ip_gw3=dict(type="ipv4", default=""),
                secondary_ip_gw4=dict(type="ipv4", default=""),
                trm_enable=dict(type="bool", default=False),
                route_target_both=dict(type="bool", default=False),
                l3gw_on_border=dict(type="bool", default=False),
                netflow_enable=dict(type="bool", default=False),
                intfvlan_nf_monitor=dict(type="str"),
                vlan_nf_monitor=dict(type="str"),
            )
            att_spec = dict(
                ip_address=dict(required=True, type="str"),
                ports=dict(required=True, type="list", default=[]),
                deploy=dict(type="bool", default=True),
            )

            if self.config:
                msg = None
                # Validate net params
                valid_net, invalid_params = validate_list_of_dicts(
                    self.config, net_spec
                )
                for net in valid_net:
                    if net.get("attach"):
                        valid_att, invalid_att = validate_list_of_dicts(
                            net["attach"], att_spec
                        )
                        net["attach"] = valid_att
                        invalid_params.extend(invalid_att)

                    if net.get("is_l2only", False) is True:
                        if (
                            net.get("vrf_name", "") is None
                            or net.get("vrf_name", "") == ""
                        ):
                            net["vrf_name"] = "NA"

                    self.validated.append(net)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format(
                        "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=msg)

        else:

            # If ingress replication is enabled multicast group address should be set to "" as default.
            # If ingress replication is not enabled, the default value for multicast group address
            # is different for DCNM and NDFC.
            if self.fabric_det.get("replicationMode") == "Ingress":
                mcast_group_addr = ""
            elif self.dcnm_version > 11:
                mcast_group_addr = "239.1.1.1"
            else:
                mcast_group_addr = "239.1.1.0"

            net_spec = dict(
                net_name=dict(required=True, type="str", length_max=64),
                net_id=dict(type="int", range_max=16777214),
                vrf_name=dict(type="str", length_max=32),
                attach=dict(type="list"),
                deploy=dict(type="bool", default=True),
                gw_ip_subnet=dict(type="ipv4_subnet", default=""),
                vlan_id=dict(type="int", range_max=4094),
                routing_tag=dict(type="int", default=12345, range_max=4294967295),
                net_template=dict(type="str", default="Default_Network_Universal"),
                net_extension_template=dict(
                    type="str", default="Default_Network_Extension_Universal"
                ),
                is_l2only=dict(type="bool", default=False),
                vlan_name=dict(type="str", length_max=128),
                int_desc=dict(type="str", length_max=258),
                mtu_l3intf=dict(type="int", range_min=68, range_max=9216),
                arp_suppress=dict(type="bool", default=False),
                dhcp_srvr1_ip=dict(type="ipv4", default=""),
                dhcp_srvr2_ip=dict(type="ipv4", default=""),
                dhcp_srvr3_ip=dict(type="ipv4", default=""),
                dhcp_srvr1_vrf=dict(type="str", length_max=32),
                dhcp_srvr2_vrf=dict(type="str", length_max=32),
                dhcp_srvr3_vrf=dict(type="str", length_max=32),
                dhcp_loopback_id=dict(type="int", range_min=0, range_max=1023),
                multicast_group_address=dict(type="ipv4", default=mcast_group_addr),
                gw_ipv6_subnet=dict(type="ipv6_subnet", default=""),
                secondary_ip_gw1=dict(type="ipv4", default=""),
                secondary_ip_gw2=dict(type="ipv4", default=""),
                secondary_ip_gw3=dict(type="ipv4", default=""),
                secondary_ip_gw4=dict(type="ipv4", default=""),
                trm_enable=dict(type="bool", default=False),
                route_target_both=dict(type="bool", default=False),
                l3gw_on_border=dict(type="bool", default=False),
                netflow_enable=dict(type="bool", default=False),
                intfvlan_nf_monitor=dict(type="str"),
                vlan_nf_monitor=dict(type="str"),
            )
            att_spec = dict(
                ip_address=dict(required=True, type="str"),
                ports=dict(required=True, type="list"),
                deploy=dict(type="bool", default=True),
            )

            if self.config:
                msg = None
                # Validate net params
                valid_net, invalid_params = validate_list_of_dicts(
                    self.config, net_spec
                )
                for net in valid_net:
                    if net.get("attach"):
                        valid_att, invalid_att = validate_list_of_dicts(
                            net["attach"], att_spec
                        )
                        net["attach"] = valid_att
                        for attach in net["attach"]:
                            attach["deploy"] = net["deploy"]
                            if attach.get("ports"):
                                attach["ports"] = [port.capitalize() for port in attach["ports"]]
                        invalid_params.extend(invalid_att)

                    if state != "deleted":
                        if net.get("is_l2only", False) is True:
                            if (
                                net.get("vrf_name", "") is not None
                                and net.get("vrf_name", "") != ""
                            ):
                                invalid_params.append(
                                    "vrf_name should not be specified for L2 Networks"
                                )
                            else:
                                net["vrf_name"] = "NA"
                        else:
                            if net.get("vrf_name", "") is None:
                                invalid_params.append(
                                    "vrf_name is required for L3 Networks"
                                )

                        if (
                            (net.get("dhcp_srvr1_ip") and not net.get("dhcp_srvr1_vrf"))
                            or (
                                net.get("dhcp_srvr1_vrf")
                                and not net.get("dhcp_srvr1_ip")
                            )
                            or (
                                net.get("dhcp_srvr2_ip")
                                and not net.get("dhcp_srvr2_vrf")
                            )
                            or (
                                net.get("dhcp_srvr2_vrf")
                                and not net.get("dhcp_srvr2_ip")
                            )
                            or (
                                net.get("dhcp_srvr3_ip")
                                and not net.get("dhcp_srvr3_vrf")
                            )
                            or (
                                net.get("dhcp_srvr3_vrf")
                                and not net.get("dhcp_srvr3_ip")
                            )
                        ):
                            invalid_params.append(
                                "DHCP server IP should be specified along with DHCP server VRF"
                            )

                        if self.dcnm_version == 11:
                            if net.get("netflow_enable") or net.get("intfvlan_nf_monitor") or net.get("vlan_nf_monitor"):
                                invalid_params.append(
                                    "Netflow configurations are supported only on NDFC"
                                )

                    self.validated.append(net)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format(
                        "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=msg)

            else:
                state = self.params["state"]
                msg = None

                if (
                    state == "merged"
                    or state == "overridden"
                    or state == "replaced"
                    or state == "query"
                ):
                    msg = "config: element is mandatory for this state {0}".format(
                        state
                    )

            if msg:
                self.module.fail_json(msg=msg)

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

        # Donot Rollback for Multi-site fabrics
        if self.is_ms_fabric:
            self.failed_to_rollback = True
            self.module.fail_json(msg=resp)
            return

        # Implementing a per task rollback logic here so that we rollback DCNM to the have state
        # whenever there is a failure in any of the APIs.
        # The idea would be to run overridden state with want=have and have=dcnm_state
        self.want_create = self.have_create
        self.want_attach = self.have_attach
        self.want_deploy = self.have_deploy

        self.have_create = []
        self.have_attach = []
        self.have_deploy = {}
        self.get_have()
        self.get_diff_override()

        self.push_to_remote(True)

        if self.failed_to_rollback:
            msg1 = "FAILED - Attempted rollback of the task has failed, may need manual intervention"
        else:
            msg1 = "SUCCESS - Attempted rollback of the task has succeeded"

        res = copy.deepcopy(resp)
        if isinstance(res, str):
            self.module.fail_json(msg=res)

        res.update({"ROLLBACK_RESULT": msg1})

        if not resp.get("DATA"):
            data = copy.deepcopy(resp.get("DATA"))
            if data.get("stackTrace"):
                data.update(
                    {"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"}
                )
                res.update({"DATA": data})

        if self.module._verbosity >= 5:
            self.module.fail_json(msg=res)

        self.module.fail_json(msg=res)

    def dcnm_update_network_information(self, want, have, cfg):

        if cfg.get("vrf_name", None) is None:
            want["vrf"] = have["vrf"]

        if cfg.get("net_id", None) is None:
            want["networkId"] = have["networkId"]

        if cfg.get("net_template", None) is None:
            want["networkTemplate"] = have["networkTemplate"]

        if cfg.get("net_extension_template", None) is None:
            want["networkExtensionTemplate"] = have["networkExtensionTemplate"]

        json_to_dict_want = json.loads(want["networkTemplateConfig"])
        json_to_dict_have = json.loads(have["networkTemplateConfig"])

        if cfg.get("vlan_id", None) is None:
            json_to_dict_want["vlanId"] = json_to_dict_have["vlanId"]
            if json_to_dict_want["vlanId"] != "":
                json_to_dict_want["vlanId"] = int(json_to_dict_want["vlanId"])

        if cfg.get("routing_tag", None) is None:
            json_to_dict_want["tag"] = json_to_dict_have["tag"]
            if json_to_dict_want["tag"] != "":
                json_to_dict_want["tag"] = int(json_to_dict_want["tag"])

        if cfg.get("gw_ip_subnet", None) is None:
            json_to_dict_want["gatewayIpAddress"] = json_to_dict_have[
                "gatewayIpAddress"
            ]

        if cfg.get("is_l2only", None) is None:
            json_to_dict_want["isLayer2Only"] = json_to_dict_have["isLayer2Only"]
            if str(json_to_dict_want["isLayer2Only"]).lower() == "true":
                json_to_dict_want["isLayer2Only"] = True
            elif str(json_to_dict_want["isLayer2Only"]).lower() == "false":
                json_to_dict_want["isLayer2Only"] = False

        if cfg.get("vlan_name", None) is None:
            json_to_dict_want["vlanName"] = json_to_dict_have["vlanName"]

        if cfg.get("int_desc", None) is None:
            json_to_dict_want["intfDescription"] = json_to_dict_have["intfDescription"]

        if cfg.get("mtu_l3intf", None) is None:
            json_to_dict_want["mtu"] = json_to_dict_have["mtu"]
            if json_to_dict_want["mtu"] != "":
                json_to_dict_want["mtu"] = int(json_to_dict_want["mtu"])

        if cfg.get("arp_suppress", None) is None:
            json_to_dict_want["suppressArp"] = json_to_dict_have["suppressArp"]
            if str(json_to_dict_want["suppressArp"]).lower() == "true":
                json_to_dict_want["suppressArp"] = True
            elif str(json_to_dict_want["suppressArp"]).lower() == "false":
                json_to_dict_want["suppressArp"] = False

        if cfg.get("dhcp_srvr1_ip", None) is None:
            json_to_dict_want["dhcpServerAddr1"] = json_to_dict_have["dhcpServerAddr1"]

        if cfg.get("dhcp_srvr2_ip", None) is None:
            json_to_dict_want["dhcpServerAddr2"] = json_to_dict_have["dhcpServerAddr2"]

        if cfg.get("dhcp_srvr3_ip", None) is None:
            json_to_dict_want["dhcpServerAddr3"] = json_to_dict_have["dhcpServerAddr3"]

        if cfg.get("dhcp_srvr1_vrf", None) is None:
            json_to_dict_want["vrfDhcp"] = json_to_dict_have["vrfDhcp"]

        if cfg.get("dhcp_srvr2_vrf", None) is None:
            json_to_dict_want["vrfDhcp2"] = json_to_dict_have["vrfDhcp2"]

        if cfg.get("dhcp_srvr3_vrf", None) is None:
            json_to_dict_want["vrfDhcp3"] = json_to_dict_have["vrfDhcp3"]

        if cfg.get("dhcp_loopback_id", None) is None:
            json_to_dict_want["loopbackId"] = json_to_dict_have["loopbackId"]

        if cfg.get("multicast_group_address", None) is None:
            json_to_dict_want["mcastGroup"] = json_to_dict_have["mcastGroup"]

        if cfg.get("gw_ipv6_subnet", None) is None:
            json_to_dict_want["gatewayIpV6Address"] = json_to_dict_have["gatewayIpV6Address"]

        if cfg.get("secondary_ip_gw1", None) is None:
            json_to_dict_want["secondaryGW1"] = json_to_dict_have["secondaryGW1"]

        if cfg.get("secondary_ip_gw2", None) is None:
            json_to_dict_want["secondaryGW2"] = json_to_dict_have["secondaryGW2"]

        if cfg.get("secondary_ip_gw3", None) is None:
            json_to_dict_want["secondaryGW3"] = json_to_dict_have["secondaryGW3"]

        if cfg.get("secondary_ip_gw4", None) is None:
            json_to_dict_want["secondaryGW4"] = json_to_dict_have["secondaryGW4"]

        if cfg.get("trm_enable", None) is None:
            json_to_dict_want["trmEnabled"] = json_to_dict_have["trmEnabled"]
            if str(json_to_dict_want["trmEnabled"]).lower() == "true":
                json_to_dict_want["trmEnabled"] = True
            else:
                json_to_dict_want["trmEnabled"] = False

        if cfg.get("route_target_both", None) is None:
            json_to_dict_want["rtBothAuto"] = json_to_dict_have["rtBothAuto"]
            if str(json_to_dict_want["rtBothAuto"]).lower() == "true":
                json_to_dict_want["rtBothAuto"] = True
            else:
                json_to_dict_want["rtBothAuto"] = False

        if cfg.get("l3gw_on_border", None) is None:
            json_to_dict_want["enableL3OnBorder"] = json_to_dict_have["enableL3OnBorder"]
            if str(json_to_dict_want["enableL3OnBorder"]).lower() == "true":
                json_to_dict_want["enableL3OnBorder"] = True
            else:
                json_to_dict_want["enableL3OnBorder"] = False

        if self.dcnm_version > 11:
            if cfg.get("netflow_enable", None) is None:
                json_to_dict_want["ENABLE_NETFLOW"] = json_to_dict_have["ENABLE_NETFLOW"]
                if str(json_to_dict_want["ENABLE_NETFLOW"]).lower() == "true":
                    json_to_dict_want["ENABLE_NETFLOW"] = True
                else:
                    json_to_dict_want["ENABLE_NETFLOW"] = False

            if cfg.get("intfvlan_nf_monitor", None) is None:
                json_to_dict_want["SVI_NETFLOW_MONITOR"] = json_to_dict_have["SVI_NETFLOW_MONITOR"]

            if cfg.get("vlan_nf_monitor", None) is None:
                json_to_dict_want["VLAN_NETFLOW_MONITOR"] = json_to_dict_have["VLAN_NETFLOW_MONITOR"]

        want.update({"networkTemplateConfig": json.dumps(json_to_dict_want)})

    def update_want(self):
        """
        Routine to compare want and have and make approriate changes to want. This routine checks the existing
        information with the config from playbook and populates the payloads in self.want apropriately.
        This routine updates self.want with final paylload information after comparing self.want and self.have and
        the playbook information.

        Parameters:
            None

        Returns:
            None
        """

        # only for 'merged' state we need to update the objects that are not included in playbook with
        # values from self.have.

        if self.module.params["state"] != "merged":
            return

        if self.want_create == []:
            return

        for net in self.want_create:

            # Get the matching have to copy values if required
            match_have = [
                have
                for have in self.have_create
                if ((net["networkName"] == have["networkName"]))
            ]
            if match_have == []:
                continue

            # Get the network from self.config to check if a particular object is included or not
            match_cfg = [
                cfg for cfg in self.config if ((net["networkName"] == cfg["net_name"]))
            ]
            if match_cfg == []:
                continue

            self.dcnm_update_network_information(net, match_have[0], match_cfg[0])


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

    dcnm_net = DcnmNetwork(module)

    if not dcnm_net.ip_sn:
        module.fail_json(
            msg="Fabric {0} missing on DCNM or does not have any switches".format(
                dcnm_net.fabric
            )
        )

    dcnm_net.validate_input()

    dcnm_net.get_want()
    dcnm_net.get_have()

    warn_msg = None

    # self.want would have defaulted all optional objects not included in playbook. But the way
    # these objects are handled is different between 'merged' and 'replaced' states. For 'merged'
    # state, objects not included in the playbook must be left as they are and for state 'replaced'
    # they must be purged or defaulted.
    dcnm_net.update_want()

    if module.params["state"] == "merged":
        warn_msg = dcnm_net.get_diff_merge()

    if module.params["state"] == "replaced":
        warn_msg = dcnm_net.get_diff_replace()

    if module.params["state"] == "overridden":
        warn_msg = dcnm_net.get_diff_override()

    if module.params["state"] == "deleted":
        dcnm_net.get_diff_delete()

    if module.params["state"] == "query":
        dcnm_net.get_diff_query()
        dcnm_net.result["response"] = dcnm_net.query

    dcnm_net.result["warnings"].append(warn_msg) if warn_msg else []

    if (
        dcnm_net.diff_create
        or dcnm_net.diff_create_quick
        or dcnm_net.diff_attach
        or dcnm_net.diff_deploy
        or dcnm_net.diff_delete
        or dcnm_net.diff_create_update
        or dcnm_net.diff_detach
        or dcnm_net.diff_undeploy
    ):
        dcnm_net.result["changed"] = True
    else:
        module.exit_json(**dcnm_net.result)

    dcnm_net.format_diff()
    dcnm_net.result["diff"] = dcnm_net.diff_input_format

    if module.check_mode:
        dcnm_net.result["changed"] = False
        module.exit_json(**dcnm_net.result)

    dcnm_net.push_to_remote()

    module.exit_json(**dcnm_net.result)


if __name__ == "__main__":
    main()
