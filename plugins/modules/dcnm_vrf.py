#!/usr/bin/python
#
# Copyright (c) 2020-2022 Cisco and/or its affiliates.
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
__author__ = (
    "Shrishail Kariyappanavar, Karthik Babu Harichandra Babu, Praveen Ramoorthy"
)

DOCUMENTATION = """
---
module: dcnm_vrf
short_description: Add and remove VRFs from a DCNM managed VXLAN fabric.
version_added: "0.9.0"
description:
    - "Add and remove VRFs and VRF Lite Extension from a DCNM managed VXLAN fabric."
    - "In Multisite fabrics, VRFs can be created only on Multisite fabric"
    - "In Multisite fabrics, VRFs cannot be created on member fabric"
author: Shrishail Kariyappanavar(@nkshrishail), Karthik Babu Harichandra Babu (@kharicha), Praveen Ramoorthy(@praveenramoorthy)
options:
  fabric:
    description:
    - Name of the target fabric for vrf operations
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
    - List of details of vrfs being managed. Not required for state deleted
    type: list
    elements: dict
    suboptions:
      vrf_name:
        description:
        - Name of the vrf being managed
        type: str
        required: true
      vrf_id:
        description:
        - ID of the vrf being managed
        type: int
        required: false
      vlan_id:
        description:
        - vlan ID for the vrf attachment
        - If not specified in the playbook, DCNM will auto-select an available vlan_id
        type: int
        required: false
      vrf_template:
        description:
        - Name of the config template to be used
        type: str
        default: 'Default_VRF_Universal'
      vrf_extension_template:
        description:
        - Name of the extension config template to be used
        type: str
        default: 'Default_VRF_Extension_Universal'
      service_vrf_template:
        description:
        - Service vrf template
        type: str
        default: None
      attach:
        description:
        - List of vrf attachment details
        type: list
        elements: dict
        suboptions:
          ip_address:
            description:
            - IP address of the switch where vrf will be attached or detached
            type: str
            required: true
            suboptions:
              vrf_lite:
                type: list
                description:
                - VRF Lite Extensions options
                elements: dict
                required: false
                suboptions:
                  peer_vrf:
                    description:
                    - VRF Name to which this extension is attached
                    type: str
                    required: true
                  interface:
                    description:
                    - Interface of the switch which is connected to the edge router
                    type: str
                    required: false
                  ipv4_addr:
                    description:
                    - IP address of the interface which is connected to the edge router
                    type: str
                    required: false
                  neighbor_ipv4:
                    description:
                    - Neighbor IP address of the edge router
                    type: str
                    required: false
                  ipv6_addr:
                    description:
                    - IPv6 address of the interface which is connected to the edge router
                    type: str
                    required: false
                  neighbor_ipv6:
                    description:
                    - Neighbor IPv6 address of the edge router
                    type: str
                    required: false
                  dot1q:
                    description:
                    - DOT1Q Id
                    type: str
                    required: false
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
#   VRFs defined in the playbook will be merged into the target fabric.
#     - If the VRF does not exist it will be added.
#     - If the VRF exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - VRFs that are not specified in the playbook will be untouched.
#
# Replaced:
#   VRFs defined in the playbook will be replaced in the target fabric.
#     - If the VRF does not exist it will be added.
#     - If the VRF exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are  not specified
#       in the playbook will be deleted or defaulted if possible.
#     - VRFs that are not specified in the playbook will be untouched.
#
# Overridden:
#   VRFs defined in the playbook will be overridden in the target fabric.
#     - If the VRF does not exist it will be added.
#     - If the VRF exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - VRFs that are not specified in the playbook will be deleted.
#
# Deleted:
#   VRFs defined in the playbook will be deleted.
#   If no VRFs are provided in the playbook, all VRFs present on that DCNM fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the VRFs listed in the playbook.
#
# rollback functionality:
# This module supports task level rollback functionality. If any task runs into failures, as part of failure
# handling, the module tries to bring the state of the DCNM back to the state captured in have structure at the
# beginning of the task execution. Following few lines provide a logical description of how this works,
# if (failure)
#     want data = have data
#     have data = get state of DCNM
#     Run the module in override state with above set of data to produce the required set of diffs
#     and push the diff payloads to DCNM.
# If rollback fails, the module does not attempt to rollback again, it just quits with appropriate error messages.

# The two VRFs below will be merged into the target fabric.
- name: Merge vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: merged
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
        deploy: true
      - ip_address: 192.168.1.225
        deploy: false
    - vrf_name: ansible-vrf-r2
      vrf_id: 9008012
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      - ip_address: 192.168.1.225

# VRF LITE Extension attached
- name: Merge vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: merged
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      - ip_address: 192.168.1.225
        vrf_lite:
         # All parameters under vrf_lite except peer_vrf are optional and
         # will be supplied by DCNM when omitted in the playbook
          - peer_vrf: test_vrf_1 # peer_vrf is mandatory
            interface: Ethernet1/16 # optional
            ipv4_addr: 10.33.0.2/30 # optional
            neighbor_ipv4: 10.33.0.1 # optional
            ipv6_addr: 2010::10:34:0:7/64 # optional
            neighbor_ipv6: 2010::10:34:0:3 # optional
            dot1q: 2 # dot1q can be got from dcnm/optional

# The two VRFs below will be replaced in the target fabric.
- name: Replace vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: replaced
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
        deploy: true
      # Delete this attachment
      # - ip_address: 192.168.1.225
      # deploy: true
      # Create the following attachment
      - ip_address: 192.168.1.226
        deploy: true
    # Dont touch this if its present on DCNM
    # - vrf_name: ansible-vrf-r2
    #   vrf_id: 9008012
    #   vrf_template: Default_VRF_Universal
    #   vrf_extension_template: Default_VRF_Extension_Universal
    #   attach:
    #   - ip_address: 192.168.1.224
    #   - ip_address: 192.168.1.225

# The two VRFs below will be overridden in the target fabric.
- name: Override vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: overridden
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
        deploy: true
      # Delete this attachment
      # - ip_address: 192.168.1.225
      #   deploy: true
      # Create the following attachment
      - ip_address: 192.168.1.226
        deploy: true
    # Delete this vrf
    # - vrf_name: ansible-vrf-r2
    #   vrf_id: 9008012
    #   vrf_template: Default_VRF_Universal
    #   vrf_extension_template: Default_VRF_Extension_Universal
    #   vlan_id: 2000
    #   service_vrf_template: null
    #   attach:
    #   - ip_address: 192.168.1.224
    #   - ip_address: 192.168.1.225

- name: Delete selected vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: deleted
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
    - vrf_name: ansible-vrf-r2
      vrf_id: 9008012
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null

- name: Delete all the vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: deleted

- name: Query vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: query
    config:
    - vrf_name: ansible-vrf-r1
    - vrf_name: ansible-vrf-r2
"""

import json
import time
import copy
import ast
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


class DcnmVrf:

    dcnm_vrf_paths = {
        11: {
            "GET_VRF": "/rest/top-down/fabrics/{}/vrfs",
            "GET_VRF_ATTACH": "/rest/top-down/fabrics/{}/vrfs/attachments?vrf-names={}",
            "GET_VRF_SWITCH": "/rest/top-down/fabrics/{}/vrfs/switches?vrf-names={}&serial-numbers={}",
            "GET_VRF_ID": "/rest/managed-pool/fabrics/{}/partitions/ids",
            "GET_VLAN": "/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_VRF_VLAN",
        },
        12: {
            "GET_VRF": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs",
            "GET_VRF_ATTACH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs/attachments?vrf-names={}",
            "GET_VRF_SWITCH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs/switches?vrf-names={}&serial-numbers={}",
            "GET_VRF_ID": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfinfo",
            "GET_VLAN": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_VRF_VLAN",
        },
    }

    def __init__(self, module):

        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))
        self.check_mode = False
        self.vrf_ext = False
        self.role = ""
        self.serial = ""
        self.have_create = []
        self.want_create = []
        self.diff_create = []
        self.diff_create_update = []
        # This variable is created specifically to hold all the create payloads which are missing a
        # vrfId. These payloads are sent to DCNM out of band (basically in the get_diff_merge())
        # We lose diffs for these without this variable. The content stored here will be helpful for
        # cases like "check_mode" and to print diffs[] in the output of each task.
        self.diff_create_quick = []
        self.have_attach = []
        self.want_attach = []
        self.diff_attach = []
        self.validated = []
        # diff_detach is to list all attachments of a vrf being deleted, especially for state: OVERRIDDEN
        # The diff_detach and delete operations have to happen before create+attach+deploy for vrfs being created.
        # This is specifically to address cases where VLAN from a vrf which is being deleted is used for another
        # vrf. Without this additional logic, the create+attach+deploy go out first and complain the VLAN is already
        # in use.
        self.diff_detach = []
        self.have_deploy = {}
        self.want_deploy = {}
        self.diff_deploy = {}
        self.diff_undeploy = {}
        self.diff_delete = {}
        self.vrflitevalues = {}
        self.diff_input_format = []
        self.query = []
        self.dcnm_version = dcnm_version_supported(self.module)
        self.inventory_data = get_fabric_inventory_details(self.module, self.fabric)
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        self.fabric_data = get_fabric_details(self.module, self.fabric)
        self.fabric_type = self.fabric_data.get("fabricType")
        self.ip_fab, self.sn_fab = get_ip_sn_fabric_dict(self.inventory_data)
        if self.dcnm_version > 12:
            self.paths = self.dcnm_vrf_paths[12]
        else:
            self.paths = self.dcnm_vrf_paths[self.dcnm_version]

        self.result = dict(changed=False, diff=[], response=[])

        self.failed_to_rollback = False
        self.WAIT_TIME_FOR_DELETE_LOOP = 5  # in seconds

    def diff_for_attach_deploy(self, want_a, have_a):

        attach_list = []

        if not want_a:
            return attach_list

        dep_vrf = False
        for want in want_a:
            found = False
            if have_a:
                for have in have_a:
                    if want["serialNumber"] == have["serialNumber"]:
                        if (
                            want["extensionValues"] != ""
                            and have["extensionValues"] != ""
                        ):
                            want_ext_values = want["extensionValues"]
                            want_ext_values = ast.literal_eval(want_ext_values)
                            have_ext_values = have["extensionValues"]
                            have_ext_values = ast.literal_eval(have_ext_values)

                            want_e = ast.literal_eval(want_ext_values["VRF_LITE_CONN"])
                            have_e = ast.literal_eval(have_ext_values["VRF_LITE_CONN"])

                            if (
                                want_e["VRF_LITE_CONN"][0]["IF_NAME"]
                                == have_e["VRF_LITE_CONN"][0]["IF_NAME"]
                            ):
                                if (
                                    want_e["VRF_LITE_CONN"][0]["DOT1Q_ID"]
                                    == have_e["VRF_LITE_CONN"][0]["DOT1Q_ID"]
                                ):
                                    if (
                                        want_e["VRF_LITE_CONN"][0]["IP_MASK"]
                                        == have_e["VRF_LITE_CONN"][0]["IP_MASK"]
                                    ):
                                        if (
                                            want_e["VRF_LITE_CONN"][0]["NEIGHBOR_IP"]
                                            == have_e["VRF_LITE_CONN"][0]["NEIGHBOR_IP"]
                                        ):
                                            if (
                                                want_e["VRF_LITE_CONN"][0]["IPV6_MASK"]
                                                == have_e["VRF_LITE_CONN"][0][
                                                    "IPV6_MASK"
                                                ]
                                            ):
                                                if (
                                                    want_e["VRF_LITE_CONN"][0][
                                                        "IPV6_NEIGHBOR"
                                                    ]
                                                    == have_e["VRF_LITE_CONN"][0][
                                                        "IPV6_NEIGHBOR"
                                                    ]
                                                ):
                                                    if (
                                                        want_e["VRF_LITE_CONN"][0][
                                                            "PEER_VRF_NAME"
                                                        ]
                                                        == have_e["VRF_LITE_CONN"][0][
                                                            "PEER_VRF_NAME"
                                                        ]
                                                    ):
                                                        found = True

                        elif (
                            want["extensionValues"] != ""
                            or have["extensionValues"] != ""
                        ):
                            found = False
                        else:
                            found = True

                            # When the attachment is to be detached and undeployed, ignore any changes
                            # to the attach section in the want(i.e in the playbook).
                            if want.get("isAttached") is not None:
                                if bool(have["isAttached"]) is not bool(
                                    want["isAttached"]
                                ):
                                    del want["isAttached"]
                                    attach_list.append(want)
                                    continue

                            if bool(have["deployment"]) is not bool(want["deployment"]):
                                dep_vrf = True

            if not found:
                if bool(want["isAttached"]):
                    del want["isAttached"]
                    attach_list.append(want)

        return attach_list, dep_vrf

    def update_attach_params(self, attach, vrf_name, deploy, vlanId):

        if not attach:
            return {}

        serial = ""
        attach["ip_address"] = dcnm_get_ip_addr_info(
            self.module, attach["ip_address"], None, None
        )
        for ip, ser in self.ip_sn.items():
            if ip == attach["ip_address"]:
                serial = ser
                self.serial = ser

        if not serial:
            self.module.fail_json(
                msg="Fabric: {0} does not have the switch: {1}".format(
                    self.fabric, attach["ip_address"]
                )
            )

        role = self.inventory_data[attach["ip_address"]].get("switchRole")
        self.role = role

        if role.lower() == "spine" or role.lower() == "super spine":
            msg = "VRFs cannot be attached to switch {0} with role {1}".format(
                attach["ip_address"], role
            )
            self.module.fail_json(msg=msg)

        ext_values = {}
        if attach["vrf_lite"]:
            """Before apply the vrf_lite config, need double check if the swtich role is started wth Border"""
            r = re.search(r"\bborder\b", role.lower())
            if not r:
                msg = "VRF LITE cannot be attached to switch {0} with role {1}".format(
                    attach["ip_address"], role
                )
                self.module.fail_json(msg=msg)

            at_lite = attach["vrf_lite"]
            for a_l in at_lite:
                if (
                    a_l["interface"]
                    and a_l["dot1q"]
                    and a_l["ipv4_addr"]
                    and a_l["neighbor_ipv4"]
                    and a_l["ipv6_addr"]
                    and a_l["neighbor_ipv6"]
                    and a_l["peer_vrf"]
                ):

                    """if all the elements are provided by the user in the playbook fill the extension values"""
                    vrflite_con = {}
                    vrflite_con["VRF_LITE_CONN"] = []
                    vrflite_con["VRF_LITE_CONN"].append({})

                    vrflite_con["VRF_LITE_CONN"][0]["IF_NAME"] = a_l["interface"]
                    vrflite_con["VRF_LITE_CONN"][0]["DOT1Q_ID"] = str(a_l["dot1q"])
                    vrflite_con["VRF_LITE_CONN"][0]["IP_MASK"] = a_l["ipv4_addr"]
                    vrflite_con["VRF_LITE_CONN"][0]["NEIGHBOR_IP"] = a_l[
                        "neighbor_ipv4"
                    ]
                    vrflite_con["VRF_LITE_CONN"][0]["NEIGHBOR_ASN"] = "65535"
                    vrflite_con["VRF_LITE_CONN"][0]["IPV6_MASK"] = a_l["ipv6_addr"]
                    vrflite_con["VRF_LITE_CONN"][0]["IPV6_NEIGHBOR"] = a_l[
                        "neighbor_ipv6"
                    ]
                    vrflite_con["VRF_LITE_CONN"][0]["AUTO_VRF_LITE_FLAG"] = "false"
                    vrflite_con["VRF_LITE_CONN"][0]["PEER_VRF_NAME"] = a_l["peer_vrf"]
                    vrflite_con["VRF_LITE_CONN"][0][
                        "VRF_LITE_JYTHON_TEMPLATE"
                    ] = "Ext_VRF_Lite_Jython"
                    ext_values["VRF_LITE_CONN"] = json.dumps(vrflite_con)

                    ms_con = {}
                    ms_con["MULTISITE_CONN"] = []
                    ext_values["MULTISITE_CONN"] = json.dumps(ms_con)

                    self.vrflitevalues = ext_values
                    self.vrf_ext = True

        attach.update({"fabric": self.fabric})
        attach.update({"vrfName": vrf_name})
        attach.update({"vlan": vlanId})
        attach.update({"deployment": deploy})
        attach.update({"isAttached": True})
        attach.update({"serialNumber": serial})
        if self.vrf_ext:
            attach.update({"extensionValues": json.dumps(ext_values).replace(" ", "")})
            attach.update(
                {
                    "instanceValues": '{"loopbackId":"","loopbackIpAddress":"","loopbackIpV6Address":""}'
                }
            )
            del attach["vrf_lite"]
        else:
            attach.update({"extensionValues": ""})
            attach.update({"instanceValues": ""})
        attach.update({"freeformConfig": ""})
        if "deploy" in attach:
            del attach["deploy"]
        del attach["ip_address"]

        return attach

    def diff_for_create(self, want, have):

        if not have:
            return {}

        create = {}

        json_to_dict_want = json.loads(want["vrfTemplateConfig"])
        json_to_dict_have = json.loads(have["vrfTemplateConfig"])

        vlanId_want = str(json_to_dict_want.get("vlanId", ""))
        vlanId_have = json_to_dict_have.get("vlanId", "")

        if vlanId_want != "0":

            if want["vrfId"] is not None and have["vrfId"] != want["vrfId"]:
                self.module.fail_json(
                    msg="vrf_id for vrf:{0} cant be updated to a different value".format(
                        want["vrfName"]
                    )
                )
            elif (
                have["serviceVrfTemplate"] != want["serviceVrfTemplate"]
                or have["vrfTemplate"] != want["vrfTemplate"]
                or have["vrfExtensionTemplate"] != want["vrfExtensionTemplate"]
                or vlanId_have != vlanId_want
            ):

                if want["vrfId"] is None:
                    # The vrf updates with missing vrfId will have to use existing
                    # vrfId from the instance of the same vrf on DCNM.
                    want["vrfId"] = have["vrfId"]
                create = want
            else:
                pass

        else:

            if want["vrfId"] is not None and have["vrfId"] != want["vrfId"]:
                self.module.fail_json(
                    msg="vrf_id for vrf:{0} cant be updated to a different value".format(
                        want["vrfName"]
                    )
                )
            elif (
                have["serviceVrfTemplate"] != want["serviceVrfTemplate"]
                or have["vrfTemplate"] != want["vrfTemplate"]
                or have["vrfExtensionTemplate"] != want["vrfExtensionTemplate"]
            ):

                if want["vrfId"] is None:
                    # The vrf updates with missing vrfId will have to use existing
                    # vrfId from the instance of the same vrf on DCNM.
                    want["vrfId"] = have["vrfId"]
                create = want
            else:
                pass

        return create

    def update_create_params(self, vrf, vlanId=""):

        if not vrf:
            return vrf

        v_template = vrf.get("vrf_template", "Default_VRF_Universal")
        ve_template = vrf.get(
            "vrf_extension_template", "Default_VRF_Extension_Universal"
        )
        src = None
        s_v_template = vrf.get("service_vrf_template", None)

        vrf_upd = {
            "fabric": self.fabric,
            "vrfName": vrf["vrf_name"],
            "vrfTemplate": v_template,
            "vrfExtensionTemplate": ve_template,
            "vrfId": vrf.get(
                "vrf_id", None
            ),  # vrf_id will be auto generated in get_diff_merge()
            "serviceVrfTemplate": s_v_template,
            "source": src,
        }
        template_conf = {
            "vrfSegmentId": vrf.get("vrf_id", None),
            "vrfName": vrf["vrf_name"],
            "vlanId": vlanId,
        }
        vrf_upd.update({"vrfTemplateConfig": json.dumps(template_conf)})

        return vrf_upd

    def get_have(self):

        have_create = []
        have_deploy = {}

        curr_vrfs = ""

        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)

        vrf_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find vrfs under fabric: {0}".format(self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not vrf_objects.get("DATA"):
            return

        for vrf in vrf_objects["DATA"]:
            curr_vrfs += vrf["vrfName"] + ","

        vrf_attach_objects = dcnm_get_url(
            self.module,
            self.fabric,
            self.paths["GET_VRF_ATTACH"],
            curr_vrfs[:-1],
            "vrfs",
        )

        if not vrf_attach_objects["DATA"]:
            return

        for vrf in vrf_objects["DATA"]:
            json_to_dict = json.loads(vrf["vrfTemplateConfig"])
            t_conf = {
                "vrfSegmentId": vrf["vrfId"],
                "vrfName": vrf["vrfName"],
                "vlanId": json_to_dict.get("vlanId", 0),
            }

            vrf.update({"vrfTemplateConfig": json.dumps(t_conf)})
            del vrf["vrfStatus"]
            have_create.append(vrf)

        upd_vrfs = ""

        for vrf_attach in vrf_attach_objects["DATA"]:
            if not vrf_attach.get("lanAttachList"):
                continue
            attach_list = vrf_attach["lanAttachList"]
            dep_vrf = ""
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
                    dep_vrf = attach["vrfName"]

                sn = attach["switchSerialNo"]
                vlan = attach["vlanId"]

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
                del attach["vrfId"]
                del attach["fabricName"]

                attach.update({"fabric": self.fabric})
                attach.update({"vlan": vlan})
                attach.update({"serialNumber": sn})
                attach.update({"deployment": deployed})
                attach.update({"extensionValues": ""})
                attach.update({"instanceValues": ""})
                attach.update({"freeformConfig": ""})
                attach.update({"isAttached": attach_state})

                """ Get the VRF LITE extension template and update it to the attach['extensionvalues']"""

                """Get the IP/Interface that is connected to edge router can be get from below query"""
                method = "GET"
                path = self.paths["GET_VRF_SWITCH"].format(
                    self.fabric, attach["vrfName"], sn
                )

                lite_objects = dcnm_send(self.module, method, path)

                if not lite_objects.get("DATA"):
                    return

                for sdl in lite_objects["DATA"]:
                    for epv in sdl["switchDetailsList"]:
                        if epv.get("extensionValues"):
                            ext_values = epv["extensionValues"]
                            ext_values = ast.literal_eval(ext_values)
                            if ext_values.get("VRF_LITE_CONN") is not None:
                                ext_values = ast.literal_eval(
                                    ext_values["VRF_LITE_CONN"]
                                )
                                for ev in ext_values["VRF_LITE_CONN"]:
                                    extension_values = {}
                                    vrflite_con = {}

                                    vrflite_con["VRF_LITE_CONN"] = []
                                    vrflite_con["VRF_LITE_CONN"].append({})
                                    vrflite_con["VRF_LITE_CONN"][0]["IF_NAME"] = ev[
                                        "IF_NAME"
                                    ]
                                    vrflite_con["VRF_LITE_CONN"][0]["DOT1Q_ID"] = str(
                                        ev["DOT1Q_ID"]
                                    )
                                    vrflite_con["VRF_LITE_CONN"][0]["IP_MASK"] = ev[
                                        "IP_MASK"
                                    ]
                                    vrflite_con["VRF_LITE_CONN"][0]["NEIGHBOR_IP"] = ev[
                                        "NEIGHBOR_IP"
                                    ]
                                    vrflite_con["VRF_LITE_CONN"][0]["IPV6_MASK"] = ev[
                                        "IPV6_MASK"
                                    ]
                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "IPV6_NEIGHBOR"
                                    ] = ev["IPV6_NEIGHBOR"]

                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "AUTO_VRF_LITE_FLAG"
                                    ] = "false"
                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "PEER_VRF_NAME"
                                    ] = attach["vrfName"]
                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "VRF_LITE_JYTHON_TEMPLATE"
                                    ] = "Ext_VRF_Lite_Jython"
                                    extension_values["VRF_LITE_CONN"] = json.dumps(
                                        vrflite_con
                                    )

                                    ms_con = {}
                                    ms_con["MULTISITE_CONN"] = []
                                    extension_values["MULTISITE_CONN"] = json.dumps(
                                        ms_con
                                    )
                                    e_values = json.dumps(extension_values).replace(
                                        " ", ""
                                    )

                                    attach.update({"extensionValues": e_values})

            if dep_vrf:
                upd_vrfs += dep_vrf + ","

        have_attach = vrf_attach_objects["DATA"]

        if upd_vrfs:
            have_deploy.update({"vrfNames": upd_vrfs[:-1]})

        self.have_create = have_create
        self.have_attach = have_attach
        self.have_deploy = have_deploy

    def get_want(self):

        want_create = []
        want_attach = []
        want_deploy = {}

        all_vrfs = ""

        if not self.config:
            return

        for vrf in self.validated:
            vrf_attach = {}
            vrfs = []

            vrf_deploy = vrf.get("deploy", True)
            if vrf.get("vlan_id"):
                vlanId = vrf.get("vlan_id")
            else:
                vlanId = 0

            want_create.append(self.update_create_params(vrf, vlanId))

            if not vrf.get("attach"):
                continue
            for attach in vrf["attach"]:
                deploy = vrf_deploy if "deploy" not in attach else attach["deploy"]
                vrfs.append(
                    self.update_attach_params(attach, vrf["vrf_name"], deploy, vlanId)
                )

            if vrfs:
                vrf_attach.update({"vrfName": vrf["vrf_name"]})
                vrf_attach.update({"lanAttachList": vrfs})
                want_attach.append(vrf_attach)

            all_vrfs += vrf["vrf_name"] + ","

        if all_vrfs:
            want_deploy.update({"vrfNames": all_vrfs[:-1]})

        self.want_create = want_create
        self.want_attach = want_attach
        self.want_deploy = want_deploy

    def get_diff_delete(self):

        diff_detach = []
        diff_undeploy = {}
        diff_delete = {}

        all_vrfs = ""

        if self.config:

            for want_c in self.want_create:
                if not next(
                    (
                        have_c
                        for have_c in self.have_create
                        if have_c["vrfName"] == want_c["vrfName"]
                    ),
                    None,
                ):
                    continue
                diff_delete.update({want_c["vrfName"]: "DEPLOYED"})

                have_a = next(
                    (
                        attach
                        for attach in self.have_attach
                        if attach["vrfName"] == want_c["vrfName"]
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
                    all_vrfs += have_a["vrfName"] + ","
            if all_vrfs:
                diff_undeploy.update({"vrfNames": all_vrfs[:-1]})

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
                    all_vrfs += have_a["vrfName"] + ","

                diff_delete.update({have_a["vrfName"]: "DEPLOYED"})
            if all_vrfs:
                diff_undeploy.update({"vrfNames": all_vrfs[:-1]})

        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

    def get_diff_override(self):

        all_vrfs = ""
        diff_delete = {}

        self.get_diff_replace()

        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_detach = self.diff_detach
        diff_deploy = self.diff_deploy
        diff_undeploy = self.diff_undeploy

        for have_a in self.have_attach:
            found = next(
                (
                    vrf
                    for vrf in self.want_create
                    if vrf["vrfName"] == have_a["vrfName"]
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
                    all_vrfs += have_a["vrfName"] + ","

                diff_delete.update({have_a["vrfName"]: "DEPLOYED"})

        if all_vrfs:
            diff_undeploy.update({"vrfNames": all_vrfs[:-1]})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

    def get_diff_replace(self):

        all_vrfs = ""

        self.get_diff_merge()
        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_deploy = self.diff_deploy

        for have_a in self.have_attach:
            r_vrf_list = []
            h_in_w = False
            for want_a in self.want_attach:
                if have_a["vrfName"] == want_a["vrfName"]:
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
                            r_vrf_list.append(a_h)
                    break

            if not h_in_w:
                found = next(
                    (
                        vrf
                        for vrf in self.want_create
                        if vrf["vrfName"] == have_a["vrfName"]
                    ),
                    None,
                )
                if found:
                    atch_h = have_a["lanAttachList"]
                    for a_h in atch_h:
                        if not bool(a_h["isAttached"]):
                            continue
                        del a_h["isAttached"]
                        a_h.update({"deployment": False})
                        r_vrf_list.append(a_h)

            if r_vrf_list:
                in_diff = False
                for d_attach in self.diff_attach:
                    if have_a["vrfName"] == d_attach["vrfName"]:
                        in_diff = True
                        d_attach["lanAttachList"].extend(r_vrf_list)
                        break

                if not in_diff:
                    r_vrf_dict = {
                        "vrfName": have_a["vrfName"],
                        "lanAttachList": r_vrf_list,
                    }
                    diff_attach.append(r_vrf_dict)
                    all_vrfs += have_a["vrfName"] + ","

        if not all_vrfs:
            self.diff_create = diff_create
            self.diff_attach = diff_attach
            self.diff_deploy = diff_deploy
            return

        if not self.diff_deploy:
            diff_deploy.update({"vrfNames": all_vrfs[:-1]})
        else:
            vrfs = self.diff_deploy["vrfNames"] + "," + all_vrfs[:-1]
            diff_deploy.update({"vrfNames": vrfs})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy

    def get_diff_merge(self):

        # Special cases:
        # 1. Auto generate vrfId if its not mentioned by user:
        #    In this case, we need to query the DCNM to get a usable ID and use it in the payload.
        #    And also, any such vrf create requests need to be pushed individually(not bulk op).

        diff_create = []
        diff_create_update = []
        diff_create_quick = []
        diff_attach = []
        diff_deploy = {}
        prev_vrf_id_fetched = None

        all_vrfs = ""

        attach_found = False
        vrf_found = False
        for want_c in self.want_create:
            vrf_found = False
            for have_c in self.have_create:
                if want_c["vrfName"] == have_c["vrfName"]:
                    vrf_found = True
                    diff = self.diff_for_create(want_c, have_c)
                    if diff:
                        diff_create_update.append(diff)
                    break
            if not vrf_found:
                vrf_id = want_c.get("vrfId", None)
                if vrf_id is None:
                    # vrfId is not provided by user.
                    # Need to query DCNM to fetch next available vrfId and use it here.
                    method = "POST"

                    attempt = 0
                    while attempt < 10:
                        attempt += 1
                        path = self.paths["GET_VRF_ID"].format(self.fabric)
                        if self.dcnm_version > 11:
                            vrf_id_obj = dcnm_send(self.module, "GET", path)
                        else:
                            vrf_id_obj = dcnm_send(self.module, method, path)

                        missing_fabric, not_ok = self.handle_response(
                            vrf_id_obj, "query_dcnm"
                        )

                        if missing_fabric or not_ok:
                            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                            msg2 = (
                                "Unable to generate vrfId for vrf: {0} "
                                "under fabric: {1}".format(
                                    want_c["vrfName"], self.fabric
                                )
                            )

                            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

                        if not vrf_id_obj["DATA"]:
                            continue

                        if self.dcnm_version == 11:
                            vrf_id = vrf_id_obj["DATA"].get("partitionSegmentId")
                        elif self.dcnm_version >= 12:
                            vrf_id = vrf_id_obj["DATA"].get("l3vni")
                        else:
                            msg = "Unsupported DCNM version: version {0}".format(
                                self.dcnm_version
                            )
                            self.module.fail_json(msg)

                        if vrf_id != prev_vrf_id_fetched:
                            want_c.update({"vrfId": vrf_id})
                            template_conf = {
                                "vrfSegmentId": vrf_id,
                                "vrfName": want_c["vrfName"],
                            }
                            want_c.update(
                                {"vrfTemplateConfig": json.dumps(template_conf)}
                            )
                            prev_vrf_id_fetched = vrf_id
                            break

                    if not vrf_id:
                        self.module.fail_json(
                            msg="Unable to generate vrfId for vrf: {0} "
                            "under fabric: {1}".format(want_c["vrfName"], self.fabric)
                        )

                    create_path = self.paths["GET_VRF"].format(self.fabric)

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

        for want_a in self.want_attach:
            dep_vrf = ""
            attach_found = False
            for have_a in self.have_attach:
                if want_a["vrfName"] == have_a["vrfName"]:
                    attach_found = True
                    diff, vrf = self.diff_for_attach_deploy(
                        want_a["lanAttachList"], have_a["lanAttachList"]
                    )
                    if diff:
                        base = want_a.copy()
                        del base["lanAttachList"]
                        base.update({"lanAttachList": diff})

                        diff_attach.append(base)
                        dep_vrf = want_a["vrfName"]
                    else:
                        if vrf:
                            dep_vrf = want_a["vrfName"]

            if not attach_found and want_a.get("lanAttachList"):
                atch_list = []
                for attach in want_a["lanAttachList"]:
                    if attach.get("isAttached"):
                        del attach["isAttached"]
                    atch_list.append(attach)
                if atch_list:
                    base = want_a.copy()
                    del base["lanAttachList"]
                    base.update({"lanAttachList": atch_list})
                    diff_attach.append(base)
                    if bool(attach["deployment"]):
                        dep_vrf = want_a["vrfName"]

            if dep_vrf:
                all_vrfs += dep_vrf + ","

        if all_vrfs:
            diff_deploy.update({"vrfNames": all_vrfs[:-1]})

        if vrf_found and not attach_found:
            self.diff_create = []
        else:
            self.diff_create = diff_create

        self.diff_create_update = diff_create_update
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_create_quick = diff_create_quick

    def format_diff(self):

        diff = []

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_quick = copy.deepcopy(self.diff_create_quick)
        diff_create_update = copy.deepcopy(self.diff_create_update)
        diff_attach = copy.deepcopy(self.diff_attach)
        diff_detach = copy.deepcopy(self.diff_detach)
        diff_deploy = (
            self.diff_deploy["vrfNames"].split(",") if self.diff_deploy else []
        )
        diff_undeploy = (
            self.diff_undeploy["vrfNames"].split(",") if self.diff_undeploy else []
        )

        diff_create.extend(diff_create_quick)
        diff_create.extend(diff_create_update)
        diff_attach.extend(diff_detach)
        diff_deploy.extend(diff_undeploy)

        for want_d in diff_create:

            found_a = next(
                (vrf for vrf in diff_attach if vrf["vrfName"] == want_d["vrfName"]),
                None,
            )

            found_c = want_d

            src = found_c["source"]
            found_c.update({"vrf_name": found_c["vrfName"]})
            found_c.update({"vrf_id": found_c["vrfId"]})
            found_c.update({"vrf_template": found_c["vrfTemplate"]})
            found_c.update({"vrf_extension_template": found_c["vrfExtensionTemplate"]})
            del found_c["source"]
            found_c.update({"source": src})
            found_c.update({"service_vrf_template": found_c["serviceVrfTemplate"]})
            found_c.update({"attach": []})

            del found_c["fabric"]
            del found_c["vrfName"]
            del found_c["vrfId"]
            del found_c["vrfTemplate"]
            del found_c["vrfExtensionTemplate"]
            del found_c["serviceVrfTemplate"]
            del found_c["vrfTemplateConfig"]

            if diff_deploy:
                diff_deploy.remove(found_c["vrf_name"])
            if not found_a:
                diff.append(found_c)
                continue

            attach = found_a["lanAttachList"]

            for a_w in attach:
                attach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w["serialNumber"]:
                        attach_d.update({"ip_address": k})
                        break
                attach_d.update({"vlan_id": a_w["vlan"]})
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

                for k, v in self.ip_sn.items():
                    if v == a_w["serialNumber"]:
                        attach_d.update({"ip_address": k})
                        break
                attach_d.update({"vlan_id": a_w["vlan"]})
                attach_d.update({"deploy": a_w["deployment"]})
                new_attach_list.append(attach_d)

            if new_attach_list:
                if diff_deploy and vrf["vrfName"] in diff_deploy:
                    diff_deploy.remove(vrf["vrfName"])
                new_attach_dict.update({"attach": new_attach_list})
                new_attach_dict.update({"vrf_name": vrf["vrfName"]})
                diff.append(new_attach_dict)

        for vrf in diff_deploy:
            new_deploy_dict = {"vrf_name": vrf}
            diff.append(new_deploy_dict)

        self.diff_input_format = diff

    def get_diff_query(self):

        method = "GET"
        path = self.paths["GET_VRF"].format(self.fabric)
        vrf_objects = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

        if (
            vrf_objects.get("ERROR") == "Not Found"
            and vrf_objects.get("RETURN_CODE") == 404
        ):
            self.module.fail_json(
                msg="Fabric {0} not present on DCNM".format(self.fabric)
            )
            return

        if missing_fabric or not_ok:
            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find VRFs under fabric: {0}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not vrf_objects["DATA"]:
            return

        if self.config:
            query = []
            for want_c in self.want_create:
                # Query the VRF
                for vrf in vrf_objects["DATA"]:

                    if want_c["vrfName"] == vrf["vrfName"]:

                        item = {"parent": {}, "attach": []}
                        item["parent"] = vrf

                        # Query the Attachment for the found VRF
                        method = "GET"
                        path = self.paths["GET_VRF_ATTACH"].format(
                            self.fabric, vrf["vrfName"]
                        )

                        vrf_attach_objects = dcnm_send(self.module, method, path)

                        missing_fabric, not_ok = self.handle_response(
                            vrf_attach_objects, "query_dcnm"
                        )

                        if missing_fabric or not_ok:
                            msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                            msg2 = (
                                "Unable to find attachments for "
                                "vrfs: {0} under fabric: {1}".format(
                                    vrf["vrfName"], self.fabric
                                )
                            )

                            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
                            return

                        if not vrf_attach_objects["DATA"]:
                            return

                        for vrf_attach in vrf_attach_objects["DATA"]:
                            if want_c["vrfName"] == vrf_attach["vrfName"]:
                                if not vrf_attach.get("lanAttachList"):
                                    continue
                                attach_list = vrf_attach["lanAttachList"]

                                for attach in attach_list:
                                    path = self.paths["GET_VRF_SWITCH"].format(
                                        self.fabric,
                                        attach["vrfName"],
                                        attach["switchSerialNo"],
                                    )
                                    lite_objects = dcnm_send(self.module, method, path)
                                    if not lite_objects.get("DATA"):
                                        return
                                    item["attach"].append(lite_objects.get("DATA")[0])
                                query.append(item)

        else:
            query = []
            # Query the VRF
            for vrf in vrf_objects["DATA"]:
                item = {"parent": {}, "attach": []}
                item["parent"] = vrf

                # Query the Attachment for the found VRF
                method = "GET"
                path = self.paths["GET_VRF_ATTACH"].format(self.fabric, vrf["vrfName"])

                vrf_attach_objects = dcnm_send(self.module, method, path)

                missing_fabric, not_ok = self.handle_response(vrf_objects, "query_dcnm")

                if missing_fabric or not_ok:
                    msg1 = "Fabric {0} not present on DCNM".format(self.fabric)
                    msg2 = (
                        "Unable to find attachments for "
                        "vrfs: {0} under fabric: {1}".format(
                            vrf["vrfName"], self.fabric
                        )
                    )

                    self.module.fail_json(msg=msg1 if missing_fabric else msg2)
                    return

                if not vrf_attach_objects["DATA"]:
                    return

                for vrf_attach in vrf_attach_objects["DATA"]:
                    if not vrf_attach.get("lanAttachList"):
                        continue
                    attach_list = vrf_attach["lanAttachList"]

                    for attach in attach_list:
                        path = self.paths["GET_VRF_SWITCH"].format(
                            self.fabric, attach["vrfName"], attach["switchSerialNo"]
                        )

                        lite_objects = dcnm_send(self.module, method, path)
                        if not lite_objects.get("DATA"):
                            return
                        item["attach"].append(lite_objects.get("DATA")[0])
                    query.append(item)

        self.query = query

    def push_to_remote(self, is_rollback=False):

        path = self.paths["GET_VRF"].format(self.fabric)

        method = "PUT"
        if self.diff_create_update:
            for vrf in self.diff_create_update:
                update_path = path + "/{0}".format(vrf["vrfName"])
                resp = dcnm_send(self.module, method, update_path, json.dumps(vrf))
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "create")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        #
        # The detach and un-deploy operations are executed before the create,attach and deploy to particularly
        # address cases where a VLAN for vrf attachment being deleted is re-used on a new vrf attachment being
        # created. This is needed specially for state: overridden
        #

        method = "POST"
        if self.diff_detach:
            detach_path = path + "/attachments"

            # Update the fabric name to specific fabric to which the switches belong for multisite fabric.
            if self.fabric_type == "MFD":
                for elem in self.diff_detach:
                    for node in elem["lanAttachList"]:
                        node["fabric"] = self.sn_fab[node["serialNumber"]]

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
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "deploy")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        del_failure = ""

        if self.diff_delete and self.wait_for_vrf_del_ready():
            method = "DELETE"
            for vrf, state in self.diff_delete.items():
                if state == "OUT-OF-SYNC":
                    del_failure += vrf + ","
                    continue
                delete_path = path + "/" + vrf
                resp = dcnm_send(self.module, method, delete_path)
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "delete")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        if del_failure:
            self.result["response"].append(
                "Deletion of vrfs {0} has failed".format(del_failure[:-1])
            )
            self.module.fail_json(msg=self.result)

        method = "POST"
        if self.diff_create:

            for vrf in self.diff_create:
                json_to_dict = json.loads(vrf["vrfTemplateConfig"])
                vlanId = json_to_dict.get("vlanId", "0")

                if vlanId == 0:
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
                    "vrfSegmentId": json_to_dict.get("vrfId", ""),
                    "vrfName": json_to_dict.get("vrfName", ""),
                    "vlanId": vlanId,
                }

                vrf.update({"vrfTemplateConfig": json.dumps(t_conf)})

                resp = dcnm_send(self.module, method, path, json.dumps(vrf))
                self.result["response"].append(resp)
                fail, self.result["changed"] = self.handle_response(resp, "create")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        if self.diff_attach:
            for d_a in self.diff_attach:
                for v_a in d_a["lanAttachList"]:
                    if v_a.get("vrf_lite"):
                        """Before apply the vrf_lite config, need double check if the switch role is started wth Border"""
                        r = re.search(r"\bborder\b", self.role.lower())
                        if not r:
                            msg = "VRF LITE cannot be attached to switch {0} with role {1}".format(
                                v_a["ip_address"], self.role
                            )
                            self.module.fail_json(msg=msg)

                        """Get the IP/Interface that is connected to edge router can be get from below query"""
                        method = "GET"
                        path = self.paths["GET_VRF_SWITCH"].format(
                            self.fabric, self.diff_attach[0]["vrfName"], self.serial
                        )

                        lite_objects = dcnm_send(self.module, method, path)

                        if not lite_objects.get("DATA"):
                            return

                        lite = lite_objects["DATA"][0]["switchDetailsList"][0][
                            "extensionPrototypeValues"
                        ]
                        ext_values = None
                        for ext_l in lite:
                            if str(ext_l.get("extensionType")) == "VRF_LITE":
                                ext_values = ext_l["extensionValues"]
                                ext_values = ast.literal_eval(ext_values)
                                extension_values = {}
                                for ad_l in v_a["vrf_lite"]:
                                    vrflite_con = {}
                                    vrflite_con["VRF_LITE_CONN"] = []
                                    vrflite_con["VRF_LITE_CONN"].append({})
                                    if ad_l["interface"]:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "IF_NAME"
                                        ] = ad_l["interface"]
                                    else:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "IF_NAME"
                                        ] = ext_values["IF_NAME"]

                                    if ad_l["dot1q"]:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "DOT1Q_ID"
                                        ] = str(ad_l["dot1q"])
                                    else:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "DOT1Q_ID"
                                        ] = str(ext_values["DOT1Q_ID"])

                                    if ad_l["ipv4_addr"]:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "IP_MASK"
                                        ] = ad_l["ipv4_addr"]
                                    else:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "IP_MASK"
                                        ] = ext_values["IP_MASK"]

                                    if ad_l["neighbor_ipv4"]:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "NEIGHBOR_IP"
                                        ] = ad_l["neighbor_ipv4"]
                                    else:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "NEIGHBOR_IP"
                                        ] = ext_values["NEIGHBOR_IP"]

                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "NEIGHBOR_ASN"
                                    ] = ext_values["NEIGHBOR_ASN"]

                                    if ad_l["ipv6_addr"]:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "IPV6_MASK"
                                        ] = ad_l["ipv6_addr"]
                                    else:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "IPV6_MASK"
                                        ] = ext_values["IPV6_MASK"]

                                    if ad_l["neighbor_ipv6"]:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "IPV6_NEIGHBOR"
                                        ] = ad_l["neighbor_ipv6"]
                                    else:
                                        vrflite_con["VRF_LITE_CONN"][0][
                                            "IPV6_NEIGHBOR"
                                        ] = ext_values["IPV6_NEIGHBOR"]

                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "AUTO_VRF_LITE_FLAG"
                                    ] = ext_values["AUTO_VRF_LITE_FLAG"]
                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "PEER_VRF_NAME"
                                    ] = ad_l["peer_vrf"]
                                    vrflite_con["VRF_LITE_CONN"][0][
                                        "VRF_LITE_JYTHON_TEMPLATE"
                                    ] = "Ext_VRF_Lite_Jython"
                                    extension_values["VRF_LITE_CONN"] = json.dumps(
                                        vrflite_con
                                    )

                                    ms_con = {}
                                    ms_con["MULTISITE_CONN"] = []
                                    extension_values["MULTISITE_CONN"] = json.dumps(
                                        ms_con
                                    )

                                    v_a["extensionValues"] = json.dumps(
                                        extension_values
                                    ).replace(" ", "")
                                    v_a[
                                        "instanceValues"
                                    ] = '{"loopbackId":"","loopbackIpAddress":"","loopbackIpV6Address":""}'
                                    del v_a["vrf_lite"]

                        if ext_values is None:
                            msg = "There is no VRF LITE capable interface on this witch {0}".format(
                                v_a["ip_address"]
                            )
                            self.module.fail_json(msg=msg)

                    else:
                        if v_a.get("vrf_lite", None) is not None:
                            del v_a["vrf_lite"]

            path = self.paths["GET_VRF"].format(self.fabric)
            method = "POST"
            attach_path = path + "/attachments"

            # Update the fabric name to specific fabric to which the switches belong for multisite fabric.
            if self.fabric_type == "MFD":
                for elem in self.diff_attach:
                    for node in elem["lanAttachList"]:
                        node["fabric"] = self.sn_fab[node["serialNumber"]]

            resp = dcnm_send(
                self.module, method, attach_path, json.dumps(self.diff_attach)
            )
            self.result["response"].append(resp)
            fail, self.result["changed"] = self.handle_response(resp, "attach")
            if fail:
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

    def wait_for_vrf_del_ready(self):

        method = "GET"
        if self.diff_delete:
            for vrf in self.diff_delete:
                state = False
                path = self.paths["GET_VRF_ATTACH"].format(self.fabric, vrf)
                while not state:
                    resp = dcnm_send(self.module, method, path)
                    state = True
                    if resp.get("DATA") is not None:
                        attach_list = resp["DATA"][0]["lanAttachList"]
                        for atch in attach_list:
                            if (
                                atch["lanAttachState"] == "OUT-OF-SYNC"
                                or atch["lanAttachState"] == "FAILED"
                            ):
                                self.diff_delete.update({vrf: "OUT-OF-SYNC"})
                                break
                            if atch["lanAttachState"] != "NA":
                                self.diff_delete.update({vrf: "DEPLOYED"})
                                state = False
                                time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                                break
                            self.diff_delete.update({vrf: "NA"})

            return True

    def validate_input(self):
        """Parse the playbook values, validate to param specs."""

        state = self.params["state"]

        if state == "merged" or state == "overridden" or state == "replaced":

            vrf_spec = dict(
                vrf_name=dict(required=True, type="str", length_max=32),
                vrf_id=dict(type="int", range_max=16777214),
                vrf_template=dict(type="str", default="Default_VRF_Universal"),
                vrf_extension_template=dict(
                    type="str", default="Default_VRF_Extension_Universal"
                ),
                vlan_id=dict(type="int", range_max=4094),
                source=dict(type="str", default=None),
                service_vrf_template=dict(type="str", default=None),
                attach=dict(type="list"),
                deploy=dict(type="bool", default=True),
            )
            att_spec = dict(
                ip_address=dict(required=True, type="str"),
                deploy=dict(type="bool", default=True),
                vrf_lite=dict(type="list", default=[]),
            )
            lite_spec = dict(
                interface=dict(type="str"),
                peer_vrf=dict(required=True, type="str"),
                ipv4_addr=dict(type="ipv4_subnet"),
                neighbor_ipv4=dict(type="ipv4"),
                ipv6_addr=dict(type="ipv6"),
                neighbor_ipv6=dict(type="ipv6"),
                dot1q=dict(type="int"),
            )

            msg = None
            if self.config:
                for vrf in self.config:
                    # A few user provided vrf parameters need special handling
                    # Ignore user input for src and hard code it to None
                    vrf["source"] = None
                    if not vrf.get("service_vrf_template"):
                        vrf["service_vrf_template"] = None

                    if "vrf_name" not in vrf:
                        msg = "vrf_name is mandatory under vrf parameters"

                    if "attach" in vrf and vrf["attach"]:
                        for attach in vrf["attach"]:
                            # if 'ip_address' not in attach or 'vlan_id' not in attach:
                            #     msg = "ip_address and vlan_id are mandatory under attach parameters"
                            if "ip_address" not in attach:
                                msg = "ip_address is mandatory under attach parameters"
                            if attach.get("vrf_lite"):
                                for vl in attach["vrf_lite"]:
                                    if not vl.get("peer_vrf"):
                                        msg = "peer_vrf is mandatory under attach VRF LITE parameters"

            else:
                if state == "merged" or state == "overridden" or state == "replaced":
                    msg = "config: element is mandatory for this state {0}".format(
                        state
                    )

            if msg:
                self.module.fail_json(msg=msg)

            if self.config:
                valid_vrf, invalid_params = validate_list_of_dicts(
                    self.config, vrf_spec
                )
                for vrf in valid_vrf:
                    if vrf.get("attach"):
                        # The deploy setting provided in the user parameters
                        # has the following behavior:
                        # (1) By default deploy is true
                        # (2) The global 'deploy' option for the vrf applies to
                        #     any attachments that don't have the 'deploy'
                        #     option explicity set.
                        for entry in vrf.get("attach"):
                            if "deploy" not in entry.keys() and "deploy" in vrf:
                                # This attach entry does not have a deploy key
                                # but the vrf global deploy flag is set so set
                                # it to the global 'deploy' value
                                entry["deploy"] = vrf["deploy"]
                        valid_att, invalid_att = validate_list_of_dicts(
                            vrf["attach"], att_spec
                        )
                        vrf["attach"] = valid_att

                        invalid_params.extend(invalid_att)
                        for lite in vrf.get("attach"):
                            if lite.get("vrf_lite"):
                                valid_lite, invalid_lite = validate_list_of_dicts(
                                    lite["vrf_lite"], lite_spec
                                )
                                lite["vrf_lite"] = valid_lite
                                invalid_params.extend(invalid_lite)
                    self.validated.append(vrf)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format(
                        "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=msg)

        else:

            vrf_spec = dict(
                vrf_name=dict(required=True, type="str", length_max=32),
                vrf_id=dict(type="int", range_max=16777214),
                vrf_template=dict(type="str", default="Default_VRF_Universal"),
                vrf_extension_template=dict(
                    type="str", default="Default_VRF_Extension_Universal"
                ),
                vlan_id=dict(type="int", range_max=4094),
                source=dict(type="str", default=None),
                service_vrf_template=dict(type="str", default=None),
                attach=dict(type="list"),
                deploy=dict(type="bool"),
            )
            att_spec = dict(
                ip_address=dict(required=True, type="str"),
                deploy=dict(type="bool", default=True),
                vrf_lite=dict(type="list", default=[]),
            )
            lite_spec = dict(
                interface=dict(type="str"),
                peer_vrf=dict(required=True, type="str"),
                ipv4_addr=dict(type="ipv4_subnet"),
                neighbor_ipv4=dict(type="ipv4"),
                ipv6_addr=dict(type="ipv6"),
                neighbor_ipv6=dict(type="ipv6"),
                dot1q=dict(type="int"),
            )

            if self.config:
                valid_vrf, invalid_params = validate_list_of_dicts(
                    self.config, vrf_spec
                )
                for vrf in valid_vrf:
                    if vrf.get("attach"):
                        valid_att, invalid_att = validate_list_of_dicts(
                            vrf["attach"], att_spec
                        )
                        vrf["attach"] = valid_att
                        invalid_params.extend(invalid_att)
                        for lite in vrf.get("attach"):
                            if lite.get("vrf_lite"):
                                valid_lite, invalid_lite = validate_list_of_dicts(
                                    lite["vrf_lite"], lite_spec
                                )
                                lite["vrf_lite"] = valid_lite
                                invalid_params.extend(invalid_lite)
                    self.validated.append(vrf)

                if invalid_params:
                    msg = "Invalid parameters in playbook: {0}".format(
                        "\n".join(invalid_params)
                    )
                    self.module.fail_json(msg=msg)

    def handle_response(self, res, op):

        fail = False
        changed = True

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
        if op == "deploy" and "No switches PENDING for deployment" in str(res.values()):
            changed = False

        return fail, changed

    def failure(self, resp):

        # Donot Rollback for Multi-site fabrics
        if self.fabric_type == "MFD":
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

    dcnm_vrf = DcnmVrf(module)

    if not dcnm_vrf.ip_sn:
        module.fail_json(
            msg="Fabric {0} missing on DCNM or does not have any switches".format(
                dcnm_vrf.fabric
            )
        )

    dcnm_vrf.validate_input()

    dcnm_vrf.get_want()
    dcnm_vrf.get_have()

    if module.params["state"] == "merged":
        dcnm_vrf.get_diff_merge()

    if module.params["state"] == "replaced":
        dcnm_vrf.get_diff_replace()

    if module.params["state"] == "overridden":
        dcnm_vrf.get_diff_override()

    if module.params["state"] == "deleted":
        dcnm_vrf.get_diff_delete()

    if module.params["state"] == "query":
        dcnm_vrf.get_diff_query()
        dcnm_vrf.result["response"] = dcnm_vrf.query

    dcnm_vrf.format_diff()
    dcnm_vrf.result["diff"] = dcnm_vrf.diff_input_format

    if (
        dcnm_vrf.diff_create
        or dcnm_vrf.diff_attach
        or dcnm_vrf.diff_detach
        or dcnm_vrf.diff_deploy
        or dcnm_vrf.diff_undeploy
        or dcnm_vrf.diff_delete
        or dcnm_vrf.diff_create_quick
        or dcnm_vrf.diff_create_update
    ):
        dcnm_vrf.result["changed"] = True
    else:
        module.exit_json(**dcnm_vrf.result)

    if module.check_mode:
        dcnm_vrf.result["changed"] = False
        module.exit_json(**dcnm_vrf.result)

    dcnm_vrf.push_to_remote()

    module.exit_json(**dcnm_vrf.result)


if __name__ == "__main__":
    main()
