#!/usr/bin/python
#
# Copyright (c) 2024 Cisco and/or its affiliates.
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
__author__ = "Mallik Mudigonda"

DOCUMENTATION = """
---
module: dcnm_vpc_pair
short_description: DCNM Ansible Module for managing VPC switch pairs required for VPC interfaces.
version_added: "3.5.0"
description:
    - "DCNM Ansible Module for managing VPC switch pairs."
author: Mallik Mudigonda(@mmudigon)
options:
  src_fabric:
    description:
      - Name of the target fabric for VPC switch pair operations
    type: str
    required: true
  state:
    description:
      - The required state of the configuration after module completion.
    type: str
    choices: ['merged', 'replaced', 'overridden', 'deleted', 'query', 'fetch']
    default: merged
  deploy:
    description:
      - Flag indicating if the configuration must be pushed to the switch.
    type: bool
    default: true
  config:
    description:
      - A list of dictionaries containing VPC switch pair information
    type: list
    elements: dict
    default: []
    suboptions:
      peerOneId:
        description:
          - IP Address/Host Name of Peer1 of VPC switch pair.
        type: str
        required: true

      peerTwoId:
        description:
          - IP Address/Host Name of Peer2 of VPC switch pair.
        type: str
        required: true

      templateName:
        description:
          - Name of the template which inlcudes the required parameters for creating the VPC switch pair.
          - This parameter is 'mandatory' if the fabric is of type 'LANClassic' or 'External'. It is optional
            otherwise.
        type: str
        required: true

      profile:
        description:
          - A dictionary of additional VPC switch pair related parameters that must be included while creating VPC switch pairs.
        suboptions:
          ADMIN_STATE:
            description:
              - Flag to enable/disbale administrative state of the interface.
            type: bool
            required: true

          ALLOWED_VLANS:
           description:
             - Vlans that are allowed on the VPC peer link port-channel.
           type: str
           choices: ['none', 'all', 'vlan-range(e.g., 1-2, 3-40)']
           default: all

          DOMAIN_ID:
           description:
             - VPC domain ID.
             - Minimum value is 1 and Maximum value is 1000.
           type: int
           required: true

          FABRIC_NAME:
            description:
              - Name of the target fabric for VPC switch pair operations.
            type: str
            required: true

          KEEP_ALIVE_HOLD_TIMEOUT:
            description:
              - Hold timeout to ignore stale peer keep alive messages.
              - Minimum value is 3 and Maximum value is 10
            type: int
            default: 3

          KEEP_ALIVE_VRF:
            description:
              - Name of the VRF used for keep-alive messages.
            type: str
            required: true

          PC_MODE:
            description:
              - Port channel mode.
            type: str
            choices: ['on', 'active', 'passive']
            default: active

          PEER1_DOMAIN_CONF:
            description:
              Additional CLI for PEER1 vPC Domain.
            type: str
            default: ""

          PEER1_KEEP_ALIVE_LOCAL_IP:
            description:
              - IP address of a L3 interface in non-default VRF on PEER1.
            type: str
            required: true

          PEER1_MEMBER_INTERFACES:
            description:
              - A list of member interfaces for PEER1.
            type: list
            elements: str
            default: []

          PEER1_PCID:
            description:
              - PEER1 peerlink port-channel number.
              - Minimum value is 1 and Maximum value is 4096.
            type: int
            default: 1

          PEER1_PO_CONF:
            description:
              - Additional CLI for PEER1 vPC peerlink port-channel.
            type: str
            default: ""

          PEER1_PO_DESC:
            description:
              - Description for the PEER1 port-channel.
              - Minimum length is 1 and Maximum length is 254.
            type: str
            default: ""

          PEER2_DOMAIN_CONF:
            description:
              Additional CLI for PEER2 vPC Domain.
            type: str
            default: ""

          PEER2_KEEP_ALIVE_LOCAL_IP:
            description:
              - IP address of a L3 interface in non-default VRF on PEER2.
            type: str
            required: true

          PEER2_MEMBER_INTERFACES:
            description:
              - A list of member interfaces for PEER2.
            type: list
            elements: str
            default: []

          PEER2_PCID:
            description:
              - PEER2 peerlink port-channel number.
              - Minimum value is 1 and Maximum value is 4096.
            type: int
            default: 1

          PEER2_PO_CONF:
            description:
              - Additional CLI for PEER2 vPC peerlink port-channel.
            type: str
            default: ""

          PEER2_PO_DESC:
            description:
              - Description for the PEER2 port-channel.
              - Minimum length is 1 and Maximum length is 254.
            type: str
            default: ""

  templates:
    description:
      - List of templates to be fetched.
      - This is required only if the 'state' is 'fetch'. In this case the list should contain the template names whose details.
        are to be fetched.
    type: list
    elements: str
    default: []
"""

EXAMPLES = """

# States:
# This module supports the following states:
#
# Merged:
#   VPC switch pairs defined in the playbook will be merged into the target fabric.
#
#   The VPC switch pairs listed in the playbook will be created if not already present on the DCNM
#   server. If the VPC switch pair is already present and the configuration information included
#   in the playbook is either different or not present in DCNM, then the corresponding
#   information is added to the DCNM. If a VPC switch pair  mentioned in playbook
#   is already present on DCNM and there is no difference in configuration, no operation
#   will be performed for such switch pairs.
#
# Replaced:
#   VPC switch pairs defined in the playbook will be replaced in the target fabric.
#
#   The state of the VPC switch pairs listed in the playbook will serve as source of truth for the
#   same VPC switch pairs present on the DCNM under the fabric mentioned. Additions and updations
#   will be done to bring the DCNM VPC switch pairs to the state listed in the playbook.
#   Note: Replace will only work on the VPC switch pairs mentioned in the playbook.
#
# Overridden:
#   VPC switch pairs defined in the playbook will be overridden in the target fabric.
#
#   The state of the VPC switch pairs listed in the playbook will serve as source of truth for all
#   the VPC switch pairs under the fabric mentioned. Additions and deletions will be done to bring
#   the DCNM VPC switch pairs to the state listed in the playbook. All VPC switch pairs other than the
#   ones mentioned in the playbook will be deleted.
#   Note: Override will work on the all the VPC switch pairs present in the DCNM Fabric.
#
# Deleted:
#   VPC switch pairs defined in the playbook will be deleted in the target fabric.
#
#   Deletes the list of VPC switch pairs specified in the playbook.  If the playbook does not include
#   any VPC switch pair information, then all VPC switch pairs from the fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the VPC switch pairs listed in the playbook.

# CREATE VPC SWITCH PAIR (LANClassic or External fabrics)

- name: Merge VPC switch pair paremeters
  cisco.dcnm.dcnm_vpc_pair:
    src_fabric: "test-fabric"
    deploy: true
    state: merged
    config:
      - peerOneId: 192.168.1.1
        peerTwoId: 192.168.1.2
        templateName: "vpc_pair"
        profile:
          ADMIN_STATE: True
          ALLOWED_VLANS: "all"
          DOMAIN_ID: 100
          FABRIC_NAME: test-fabric
          KEEP_ALIVE_HOLD_TIMEOUT: 3
          KEEP_ALIVE_VRF: management
          PC_MODE: active
          PEER1_DOMAIN_CONF: "graceful consistency-check"
          PEER1_KEEP_ALIVE_LOCAL_IP: 192.168.1.1
          PEER1_MEMBER_INTERFACES: e1/21,e1/22-23
          PEER1_PCID: 101
          PEER1_PO_CONF: "buffer-boost"
          PEER1_PO_DESC: "This is peer1 PC"
          PEER2_DOMAIN_CONF: "graceful consistency-check"
          PEER2_KEEP_ALIVE_LOCAL_IP: 192.168.1.2
          PEER2_MEMBER_INTERFACES: e1/21,e1/22-23
          PEER2_PCID: 102
          PEER2_PO_CONF: "buffer-boost"
          PEER2_PO_DESC: "This is peer2 PC"

# CREATE VPC SWITCH PAIR (VXLAN fabrics)

- name: Merge VPC switch pair paremeters
  cisco.dcnm.dcnm_vpc_pair:
    src_fabric: "test-fabric"
    deploy: true
    state: merged
    config:
      - peerOneId: 192.168.1.1
        peerTwoId: 192.168.1.2

# DELETE VPC SWITCH PAIR

- name: Delete VPC switch pair
  cisco.dcnm.dcnm_vpc_pair:
    src_fabric: "test-fabric"
    deploy: true
    state: deleted
    config:
      - peerOneId: 192.168.1.1
        peerTwoId: 192.168.1.2

# REPLACE VPC SWITCH PAIR (LANClassic or External fabrics)

- name: Replace VPC switch pair paremeters
  cisco.dcnm.dcnm_vpc_pair:
    src_fabric: "test-fabric"
    deploy: true
    state: merged
    config:
      - peerOneId: 192.168.1.1
        peerTwoId: 192.168.1.2
        templateName: "vpc_pair"
        profile:
          ADMIN_STATE: True
          ALLOWED_VLANS: "all"
          DOMAIN_ID: 100
          FABRIC_NAME: test-fabric
          KEEP_ALIVE_HOLD_TIMEOUT: 3
          KEEP_ALIVE_VRF: management
          PC_MODE: active
          PEER1_DOMAIN_CONF: "graceful consistency-check"
          PEER1_KEEP_ALIVE_LOCAL_IP: 192.168.1.1
          PEER1_MEMBER_INTERFACES: e1/21,e1/22-23
          PEER1_PCID: 101
          PEER1_PO_CONF: "buffer-boost"
          PEER1_PO_DESC: "This is peer1 PC"
          PEER2_DOMAIN_CONF: "graceful consistency-check"
          PEER2_KEEP_ALIVE_LOCAL_IP: 192.168.1.2
          PEER2_MEMBER_INTERFACES: e1/21,e1/22-23
          PEER2_PCID: 102
          PEER2_PO_CONF: "buffer-boost"
          PEER2_PO_DESC: "This is peer2 PC"

# OVERRIDDE VPC SWITCH PAIRS

- name: Override with a new VPC switch pair
  cisco.dcnm.dcnm_vpc_pair:
    src_fabric: "test-fabric"
    deploy: true
    state: overridden
    config:
      - peerOneId: 192.168.1.1
        peerTwoId: 192.168.1.2
        templateName: "vpc_pair"
        profile:
          ADMIN_STATE: True
          ALLOWED_VLANS: "all"
          DOMAIN_ID: 100
          FABRIC_NAME: "test-fabric"
          KEEP_ALIVE_HOLD_TIMEOUT: 3
          KEEP_ALIVE_VRF: management
          PC_MODE: active
          PEER1_KEEP_ALIVE_LOCAL_IP: 192.168.1.1
          PEER1_MEMBER_INTERFACES: e1/20
          PEER1_PCID: 101
          PEER1_PO_DESC: "This is peer1 PC"
          PEER2_KEEP_ALIVE_LOCAL_IP: 192.168.1.2
          PEER2_MEMBER_INTERFACES: e1/20
          PEER2_PCID: 102
          PEER2_PO_DESC: "This is peer2 PC"

- name: Override without any new switch pairs
  cisco.dcnm.dcnm_vpc_pair:
    src_fabric: "test-fabric"
    deploy: true
    state: overridden

# QUERY VPC SWITCH PAIRS

- name: Query VPC switch pairs - with no filters
  cisco.dcnm.dcnm_vpc_pair:
    src_fabric: "test-fabric"
    state: query

- name: Query VPC switch pairs - with both peers specified
  cisco.dcnm.dcnm_vpc_pair:
    src_fabric: "test-fabric"
    state: query
    config:
      - peerOneId: "{{ ansible_switch1 }}"
        peerTwoId: "{{ ansible_switch2 }}"

- name: Query VPC switch pairs - with one peer specified
  cisco.dcnm.dcnm_vpc_pair:
    src_fabric: "test-fabric"
    state: query
    config:
      - peerOneId: "{{ ansible_switch1 }}"
"""

# WARNING:
#   This file is automatically generated. Take a backup of your
#   manually running cg_run.py script to generate it again
#

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
    dcnm_version_supported,
    get_ip_sn_dict,
    get_fabric_inventory_details,
    get_fabric_details,
    dcnm_get_template_specs,
    dcnm_update_arg_specs,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_vpc_pair_utils import (
    dcnm_vpc_pair_utils_get_paths,
    dcnm_vpc_pair_utils_translate_config,
    dcnm_vpc_pair_utils_get_vpc_pair_info,
    dcnm_vpc_pair_utils_get_vpc_pair_payload,
    dcnm_vpc_pair_utils_update_other_information,
    dcnm_vpc_pair_utils_update_vpc_pair_information,
    dcnm_vpc_pair_utils_update_common_spec,
    dcnm_vpc_pair_utils_validate_profile,
    dcnm_vpc_pair_utils_get_matching_have,
    dcnm_vpc_pair_utils_get_matching_cfg,
    dcnm_vpc_pair_utils_merge_want_and_have,
    dcnm_vpc_pair_utils_compare_want_and_have,
    dcnm_vpc_pair_utils_get_vpc_pair_deploy_payload,
    dcnm_vpc_pair_utils_process_delete_payloads,
    dcnm_vpc_pair_utils_process_create_payloads,
    dcnm_vpc_pair_utils_process_modify_payloads,
    dcnm_vpc_pair_utils_process_deploy_payloads,
    dcnm_vpc_pair_utils_get_delete_payload,
    dcnm_vpc_pair_utils_get_delete_deploy_payload,
    dcnm_vpc_pair_utils_translate_vpc_pair_info,
    dcnm_vpc_pair_utils_get_sync_status,
    dcnm_vpc_pair_utils_get_delete_list,
    dcnm_vpc_pair_utils_get_all_filtered_vpc_pair_pairs,
    dcnm_vpc_pair_utils_validate_devices,
)


# Resource Class object which includes all the required methods and data to configure and maintain Vpc_pair
class DcnmVpcPair:
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.fabric = module.params["src_fabric"]
        self.deploy = module.params["deploy"]
        self.config = copy.deepcopy(module.params.get("config", []))
        self.vpc_pair_info = []
        self.want = []
        self.have = []
        self.diff_create = []
        self.diff_modify = []
        self.diff_delete = []
        self.diff_delete_deploy = []
        self.diff_deploy = []
        self.monitoring = []
        self.meta_switches = []
        self.arg_specs = {}
        self.fd = None
        self.changed_dict = [
            {
                "merged": [],
                "deleted": [],
                "delete_deploy": [],
                "modified": [],
                "query": [],
                "deploy": [],
                "debugs": [],
            }
        ]

        self.result = dict(changed=False, diff=[], response=[])

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("dcnm_vpc_pair.log", "a+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.write("\n")
            self.fd.flush()

    def dcnm_vpc_pair_merge_want_and_have_objects(self, want, have):

        """
        Routine to merge the 'want' and 'have' if required. If an object requires mering, then the
        values from 'want' and 'have' will be combined into one instead of overwriting.

        Parameters:
            want (dict): Object to be updated with information from have
            have (dict): Existing VPC pair information

        Returns:
            None
        """

        for key in list(want.keys()):

            # Check if <key>_defaulted is present in 'want'. If present merge the original key if
            # <key>_defaulted is True.

            if "_defaulted" in key:
                # Don't have to process these keys. They will be popped when the corresponding key is processed
                continue

            if key + "_defaulted" in want:
                # If the value of key+'_defaulted' is True, then the actual key has been copied from 'have'
                # in xxx_update_want() routine. Skip those keys. If it is False, then this key is mergeable
                # and so merge it appropriately.

                if want.get(key + "_defaulted", False) is False:
                    # NOTE: key requires a merge between 'want' and 'have'. The following utility
                    #       function must do the appropriate checks and merge the key values from 'want'
                    #       and 'have'.
                    dcnm_vpc_pair_utils_merge_want_and_have(
                        self, want, have, key
                    )
                # Remove the <key>_defaulted from want
                want.pop(key + "_defaulted")

    def dcnm_vpc_pair_merge_want_and_have(self, want, have):

        """
        Routine to check for mergeable keys in want and merge the same with whatever is already exsiting
        in have.

        Parameters:
            want (dict): Object to be updated with information from have
            have (dict): Existing VPC pair information

        Returns:
            None
        """

        defaulted_keys = []

        # Code is generated for comparing "nvPairs" objects alone. If there are other nested structures
        # in the want and have objects that need to be comapred, add the necessary code here.

        # There may be certain objects like "Freeform config" in the parameters which
        # inlcude a list of commands or parameters like member ports which inlcudes a
        # list of interfaces. During MERGE, the values from WANT should be merged
        # to values in have. Identify the actual keys in WANT and HAVE and update the
        # below block of CODE to achieve the merge

        self.dcnm_vpc_pair_merge_want_and_have_objects(want, have)

        # If "nvPairs" object is not present in 'want' or 'have' then nothing to be merged
        if (want.get("nvPairs", None) is None) or (
            (have.get("nvPairs", None) is None)
        ):
            return

        self.dcnm_vpc_pair_merge_want_and_have_objects(
            want["nvPairs"], have["nvPairs"]
        )

    def dcnm_vpc_pair_get_diff_query(self):

        """
        Routine to retrieve VPC switch pairs from controller. This routine extracts information provided by the
        user and filters the output based on that.

        Parameters:
            None

        Returns:
            None
        """

        vpc_pair_list = dcnm_vpc_pair_utils_get_all_filtered_vpc_pair_pairs(
            self
        )
        if vpc_pair_list != []:
            self.result["response"].extend(vpc_pair_list)

    def dcnm_vpc_pair_get_diff_overridden(self, cfg):

        """
        Routine to override existing VPC information with what is included in the playbook. This routine
        deletes all VPC pairs which are not part of the current config and creates new ones based on what is
        included in the playbook

        Parameters:
            cfg (dct): Configuration information from playbook

        Returns:
            None
        """

        del_list = dcnm_vpc_pair_utils_get_delete_list(self)

        # 'del_list' contains all VPC pair information in 'have' format. Use that to update delete and delte
        # deploy payloads

        for elem in del_list:
            rc = self.dcnm_vpc_pair_update_delete_payloads(elem)

        if cfg == []:
            return

        if self.want:
            # New configuration is included. Delete all existing VPC switch pairs and create new pairs as requested
            # through the configuration
            rc = self.dcnm_vpc_pair_get_diff_merge()

    def dcnm_vpc_pair_get_diff_deleted(self):

        """
        Routine to get a list of payload information that will be used to delete Vpc_pair.
        This routine updates self.diff_delete with payloads that are used to delete Vpc_pair
        from the server.

        Parameters:
            None

        Returns:
            None
        """

        if self.vpc_pair_info == []:
            # User has not included any config. Delete all existing VPC pairs from DCNM
            self.dcnm_vpc_pair_get_diff_overridden([])
            return

        for elem in self.vpc_pair_info:

            # Perform any translations that may be required on the vpc_pair_info.
            xelem = dcnm_vpc_pair_utils_translate_vpc_pair_info(self, elem)
            have = dcnm_vpc_pair_utils_get_vpc_pair_info(self, xelem)

            # Check the peering before deleting. Delete only the peering that is requested for.
            if (
                (have == [])
                or (xelem["peerOneId"] != have["peerOneId"] and xelem["peerOneId"] != have["peerTwoId"])
                or (xelem["peerTwoId"] != have["peerTwoId"] and xelem["peerTwoId"] != have["peerOneId"])
            ):
                continue

            if have != []:
                self.dcnm_vpc_pair_update_delete_payloads(have)

    def dcnm_vpc_pair_update_delete_payloads(self, have):

        # Get the delete payload based on 'have'
        del_payload = dcnm_vpc_pair_utils_get_delete_payload(self, have)

        if del_payload != {} and del_payload not in self.diff_delete:
            self.changed_dict[0]["deleted"].append(del_payload)
            self.diff_delete.append(del_payload)

        # Deploy only if deploy is requested for
        if self.deploy:
            # Some objects may require a deploy for delete operation too. If the module has such a requirement
            # get the relevant deploy payload here.
            del_deploy_payload = dcnm_vpc_pair_utils_get_delete_deploy_payload(
                self, have
            )
            if (
                del_deploy_payload != {}
                and del_deploy_payload not in self.diff_delete_deploy
            ):
                self.changed_dict[0]["delete_deploy"].append(
                    del_deploy_payload
                )
                self.diff_delete_deploy.append(del_deploy_payload)

    def dcnm_vpc_pair_get_diff_merge(self):

        """
        Routine to populate a list of payload information in self.diff_create to create/update Vpc_pair.

        Parameters:
            None

        Returns:
            None
        """

        if not self.want:
            return

        for elem in self.want:

            rc, reasons, have = dcnm_vpc_pair_utils_compare_want_and_have(
                self, elem
            )

            if rc == "DCNM_VPC_PAIR_CREATE":
                # Object does not exists, create a new one.
                if elem not in self.diff_create:
                    self.changed_dict[0]["merged"].append(elem)
                    self.diff_create.append(elem)
            if rc == "DCNM_VPC_PAIR_MERGE":
                # Object already exists, and needs an update
                if elem not in self.diff_modify:
                    self.changed_dict[0]["modified"].append(elem)
                    self.changed_dict[0]["debugs"].append({"REASONS": reasons})

                    # Fields like CONF which are a list of commands should be handled differently in this case.
                    # For existing objects, we will have to merge the current list of commands with already existing
                    # ones in have. For replace, no need to merge them. They must be replaced with what is given.
                    if self.module.params["state"] == "merged":
                        self.dcnm_vpc_pair_merge_want_and_have(elem, have)
                    self.diff_modify.append(elem)

            # Check if "deploy" flag is True. If True, deploy the changes.
            if self.deploy:
                # Before building deploy payload, check
                #  - if something is being created
                #  - if something that is existing is being updated
                #  - if switches are in "In-Sync" state already

                sync_state = dcnm_vpc_pair_utils_get_sync_status(self, elem)

                if (
                    (rc == "DCNM_VPC_PAIR_CREATE")
                    or (rc == "DCNM_VPC_PAIR_MERGE")
                    or (sync_state != "In-Sync")
                ):
                    payload = dcnm_vpc_pair_utils_get_vpc_pair_deploy_payload(
                        self, elem
                    )
                    if payload != {} and payload not in self.diff_deploy:
                        self.diff_deploy.append(payload)

        if self.diff_deploy != []:
            self.changed_dict[0]["deploy"].extend(
                copy.deepcopy(self.diff_deploy)
            )

    def dcnm_vpc_pair_update_want(self):

        """
        This routine does the following when the state is 'merged'. For every object in self.want

            - Find a matching object from self.have
            - Find a matching object from the playbook configuration
            - Invoke update function which updates 'want' appropriatley based on the matching objects found

        Parameters:
            None

        Returns:
            None
        """

        if self.module.params["state"] != "merged":
            return

        for want in self.want:

            match_have = dcnm_vpc_pair_utils_get_matching_have(self, want)
            match_cfg = dcnm_vpc_pair_utils_get_matching_cfg(self, want)

            if match_cfg == []:
                continue

            for melem in match_have:
                dcnm_vpc_pair_utils_update_vpc_pair_information(
                    self, want, melem, match_cfg[0]
                )

    def dcnm_vpc_pair_get_want(self):

        """
        This routine updates self.want with the payload information based on the playbook configuration.

        Parameters:
            None

        Returns:
            None
        """

        if self.config == []:
            return

        if not self.vpc_pair_info:
            return

        for elem in self.vpc_pair_info:

            # If a separate payload is required for every switch included in the payload, then modify this
            # code to loop over the switches. Also the get payload routine should be modified appropriately.

            payload = self.dcnm_vpc_pair_get_payload(elem)

            if payload not in self.want:
                self.want.append(payload)

    def dcnm_vpc_pair_get_have(self):

        """
        Routine to get exisitng vpc_pair information from DCNM that matches information in self.want.
        This routine updates self.have with all the vpc_pair that match the given playbook configuration

        Parameters:
            None

        Returns:
            None
        """

        if self.want == []:
            return

        for elem in self.want:
            have = dcnm_vpc_pair_utils_get_vpc_pair_info(self, elem)

            # Check if the peers in 'want' and 'have' match. If not raise an error. This may be the case
            # when a peering already exists between, say, peer1 and peer2. Now if the playbook requests a
            # another peering, say, peer1 and peer3 or peer2 and peer4, then this should be flagged as an error.

            if have != [] and (
                (
                    elem["peerOneId"] != have["peerOneId"]
                    and elem["peerOneId"] != have["peerTwoId"]
                )
                or (
                    elem["peerTwoId"] != have["peerTwoId"]
                    and elem["peerTwoId"] != have["peerOneId"]
                )
            ):
                mesg = f"Peering {have['peerOneId']}-{have['peerTwoId']} already exists. Cannot create peering for {elem['peerOneId']}-{elem['peerTwoId']}"
                self.module.fail_json(msg=mesg)

            # In some cases, specifically on VXLAN fabrics, the peerOneId and peerTwoId will get swapped on NDFC server. The peerOneId and peerTwoId selection
            # happens based on some internal logic. Users may not be aware of which switch is peer1 and which is peer2.
            # To handle such cases transparently, we will swap the peerOneId and peerTwoId fields in WANT, to be consistent with 'have'.
            # Otherwise idempotence cases may fail.
            if have != []:
                elem["peerOneId"] = have["peerOneId"]
                elem["peerTwoId"] = have["peerTwoId"]

            if (have != []) and (have not in self.have):
                self.have.append(have)

    def dcnm_vpc_pair_validate_deleted_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        deleted state input. This routine updates self.vpc_pair_info with
        validated playbook information related to deleted state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {
            "peerOneId": {"required": "True", "type": "ipv4"},
            "peerTwoId": {"required": "True", "type": "ipv4"},
        }

        vpc_pair_info, invalid_params = validate_list_of_dicts(cfg, arg_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if vpc_pair_info:
            self.vpc_pair_info.extend(vpc_pair_info)

    def dcnm_vpc_pair_validate_query_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        query state input. This routine updates self.vpc_pair_info with
        validated playbook information related to query state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {
            "peerOneId": {"type": "ipv4"},
            "peerTwoId": {"type": "ipv4"},
        }

        vpc_pair_info, invalid_params = validate_list_of_dicts(cfg, arg_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if vpc_pair_info:
            self.vpc_pair_info.extend(vpc_pair_info)

    def dcnm_vpc_pair_validate_input(self, cfg):

        # The generator hanldes only the case where:
        #   - there are some common paremeters that are included in the playbook
        #   - and a profile which is a 'dict' and which is either based on a template or some fixed structure
        # NOTE: This code assumes that the nested structure will be under a key called 'profile'. If not modify the
        #       same appropriately.
        # This routine generates code to validate the common part and the 'profile' part which is one level nested.
        # Users must modify this code appropriately to hanlde any further nested structures that may be part
        # of playbook input.

        arg_spec = {}
        common_spec = {
            "peerOneId": {"required": "True", "type": "ipv4"},
            "peerTwoId": {"required": "True", "type": "ipv4"},
            "templateName": {"type": "str"},
            "useVirtualPeerlink": {"type": "bool"},
            "profile": {"type": "dict"},
        }

        # Even 'common_spec' may require some updates based on other information.
        dcnm_vpc_pair_utils_update_common_spec(self, common_spec)

        vpc_pair_info, invalid_params = validate_list_of_dicts(
            cfg, common_spec
        )
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if (cfg[0].get("templateName", None) is not None) and (
            cfg[0].get("profile", None) is not None
        ):
            # The following will return a combination of playbook template and the argument spec. Extract the
            # argument_spec from the combined_spec

            # Check if the arg_spec for this template is already available. If so use the cached spec. If not
            # fetch the specs
            if self.arg_specs.get(cfg[0]["templateName"], None) is None:
                combined_spec = dcnm_get_template_specs(
                    self.module, cfg[0]["templateName"], self.dcnm_version
                )
                arg_spec = combined_spec[cfg[0]["templateName"] + "_spec"]
                dcnm_update_arg_specs(cfg[0]["profile"], arg_spec)
                self.arg_specs[cfg[0]["templateName"]] = arg_spec
            else:
                arg_spec = self.arg_specs[cfg[0]["templateName"]]

        if arg_spec != {}:
            vpc_pair_profile_info = dcnm_vpc_pair_utils_validate_profile(
                self, cfg[0]["profile"], arg_spec
            )
            if vpc_pair_profile_info:
                vpc_pair_info[0]["profile"].update(vpc_pair_profile_info[0])
            else:
                vpc_pair_info[0].pop("profile")
                vpc_pair_info[0].pop("templateName")
        else:
            vpc_pair_info[0].pop("profile")
            vpc_pair_info[0].pop("templateName")

        self.vpc_pair_info.append(vpc_pair_info[0])

    def dcnm_vpc_pair_validate_all_input(self):

        """
        Routine to validate playbook input based on the state. Since each state has a different
        config structure, this routine handles the validation based on the given state

        Parameters:
            None

        Returns:
            None
        """

        if self.config == []:
            return

        cfg = []
        for item in self.config:

            citem = copy.deepcopy(item)

            cfg.append(citem)

            if self.module.params["state"] == "query":
                # config for query state is different. So validate query state differently
                self.dcnm_vpc_pair_validate_query_state_input(cfg)
            elif self.module.params["state"] == "deleted":
                # config for deleted state is different. So validate deleted state differently
                self.dcnm_vpc_pair_validate_deleted_state_input(cfg)
            else:
                self.dcnm_vpc_pair_validate_input(cfg)
            cfg.remove(citem)

    def dcnm_vpc_pair_get_payload(self, vpc_pair_info):

        """
        This routine builds the complete object payload based on the information in self.want

        Parameters:
            vpc_pair_info (dict): Object information

        Returns:
            vpc_pair_payload (dict): Object payload information populated with appropriate data from playbook config
        """

        vpc_pair_payload = dcnm_vpc_pair_utils_get_vpc_pair_payload(
            self, vpc_pair_info
        )

        return vpc_pair_payload

    def dcnm_vpc_pair_update_inventory_data(self):

        """
        Routine to update inventory data for all fabrics included in the playbook. This routine
        also updates ip_sn, sn_hn and hn_sn objetcs from the updated inventory data.

        Parameters:
            None

        Returns:
            None
        """

        processed_fabrics = []

        # Soure fabric is already processed. Add it to processed list
        processed_fabrics.append(self.fabric)

        # Based on the updated inventory_data, update ip_sn, hn_sn and sn_hn objects
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        self.sn_hn = dict([(value, key) for key, value in self.hn_sn.items()])
        self.sn_ip = dict([(value, key) for key, value in self.ip_sn.items()])

        # There may be other updates that are required based on the module requirements. Generating a
        # utility function call below ot take care of any such translations which are not common to all
        # modules

        dcnm_vpc_pair_utils_update_other_information(self)

        # Get all switches which are managable. Deploy must be avoided to all switches which are not part of this list
        managable_ip = [
            (key, self.inventory_data[key]["serialNumber"])
            for key in self.inventory_data
            if str(self.inventory_data[key]["managable"]).lower() == "true"
        ]
        managable_hosts = [
            (
                self.inventory_data[key]["logicalName"],
                self.inventory_data[key]["serialNumber"],
            )
            for key in self.inventory_data
            if str(self.inventory_data[key]["managable"]).lower() == "true"
        ]
        self.managable = dict(managable_ip + managable_hosts)

        self.meta_switches = [
            (
                key,
                self.inventory_data[key]["logicalName"],
                self.inventory_data[key]["serialNumber"],
            )
            for key in self.inventory_data
            if self.inventory_data[key]["switchRoleEnum"] is None
        ]

        # Get all fabrics which are in monitoring mode. Deploy must be avoided to all fabrics which are part of this list
        for fabric in processed_fabrics:
            path = self.paths["FABRIC_ACCESS_MODE"].format(fabric)
            resp = dcnm_send(self.module, "GET", path)

            if resp and resp["RETURN_CODE"] == 200:
                if str(resp["DATA"]["readonly"]).lower() == "true":
                    self.monitoring.append(fabric)

        # Check if source fabric is in monitoring mode. If so return an error, since fabrics in monitoring mode do not allow
        # create/modify/delete and deploy operations.
        if self.fabric in self.monitoring:
            self.module.fail_json(
                msg="Error: Source Fabric '{0}' is in Monitoring mode, No changes are allowed on the fabric\n".format(
                    self.fabric
                )
            )

    def dcnm_vpc_pair_translate_playbook_info(self, config, ip_sn, hn_sn):

        """
        Routine to translate parameters in playbook if required.
            - This routine converts the hostname information included in
              playbook to actual addresses.

        Parameters:
            config - The resource which needs translation
            ip_sn - IP address to serial number mappings
            hn_sn - hostname to serial number mappings

        Returns:
            None
        """

        if config == []:
            return

        for cfg in config:

            # Add other translations as required
            dcnm_vpc_pair_utils_translate_config(self, cfg)

            # Check if the switches included in the config are Manageable.
            dcnm_vpc_pair_utils_validate_devices(self, cfg)

    def dcnm_vpc_pair_fetch_template_details(self, template_info):

        """
        Routine to fetch details of all templates inlcuded in 'template_info'. The template information
        obtained will be formatted appropriately to represent playbook format with other details to assist
        the user to bulid the relevant playbook

        Parameters:
            config - The resource which includes playbook info
            template_info - List of template names whose details are to be fetched

        Returns:
            List of template information in playbook format
        """

        template_list = []
        for name in template_info:
            tinfo = dcnm_get_template_specs(
                self.module, name, self.dcnm_version
            )
            # While fetching template details we will not require arg_spec for the same. Remove that from
            # the result
            tinfo.pop(name + "_spec")

            if tinfo not in template_list:
                template_list.append(tinfo)

        return template_list

    def dcnm_vpc_pair_send_message_to_dcnm(self):

        """
        Routine to push payloads to DCNM server. This routine implements required error checks and retry mechanisms to handle
        transient errors. This routine checks self.diff_create, self.diff_delete lists and push appropriate requests to DCNM.

        Parameters:
            None

        Returns:
            None
        """

        resp = None
        create_flag = False
        modify_flag = False
        delete_flag = False
        deploy_flag = False

        delete_flag = dcnm_vpc_pair_utils_process_delete_payloads(self)
        create_flag = dcnm_vpc_pair_utils_process_create_payloads(self)
        modify_flag = dcnm_vpc_pair_utils_process_modify_payloads(self)
        deploy_flag = dcnm_vpc_pair_utils_process_deploy_payloads(
            self, self.diff_deploy
        )

        self.result["changed"] = (
            create_flag or modify_flag or delete_flag or deploy_flag
        )

    def dcnm_vpc_pair_update_module_info(self):

        """
        Routine to update version and fabric details

        Parameters:
            None

        Returns:
            None
        """

        self.dcnm_version = dcnm_version_supported(self.module)
        self.inventory_data = get_fabric_inventory_details(
            self.module, self.fabric
        )

        self.src_fabric_info = get_fabric_details(self.module, self.fabric)
        self.paths = dcnm_vpc_pair_utils_get_paths(self.dcnm_version)


def main():

    """ main entry point for module execution
    """
    element_spec = dict(
        src_fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict", default=[]),
        state=dict(
            type="str",
            default="merged",
            choices=[
                "merged",
                "deleted",
                "replaced",
                "overridden",
                "query",
                "fetch",
            ],
        ),
        deploy=dict(type="bool", default="true"),
        templates=dict(type="list", elements="str", default=[]),
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    dcnm_vpc_pair = DcnmVpcPair(module)

    state = module.params["state"]

    if dcnm_vpc_pair.config == []:
        if state == "merged" or state == "replaced":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_vpc_pair.config
                )
            )

    # Update the created module with version and fabric details
    dcnm_vpc_pair.dcnm_vpc_pair_update_module_info()

    # If state is 'fetch' and 'templates' is is non-empty, then the list contains template names that
    # are relevant to this module.
    # User is trying to fetch the details for all these templates that can be used to build relevant
    # playbooks. Reuturn the template details and do not proceeed further since the included playbook
    # may not be conatining all the required details for successful execution.

    if state == "fetch":
        if module.params["templates"] != []:
            temp_details = dcnm_vpc_pair.dcnm_vpc_pair_fetch_template_details(
                module.params["templates"]
            )
            dcnm_vpc_pair.result["templates"] = temp_details
        dcnm_vpc_pair.result["changed"] = False
        module.exit_json(**dcnm_vpc_pair.result)

    dcnm_vpc_pair.dcnm_vpc_pair_update_inventory_data()

    dcnm_vpc_pair.dcnm_vpc_pair_translate_playbook_info(
        dcnm_vpc_pair.config, dcnm_vpc_pair.ip_sn, dcnm_vpc_pair.hn_sn
    )

    dcnm_vpc_pair.dcnm_vpc_pair_validate_all_input()

    if (
        module.params["state"] != "query"
        and module.params["state"] != "deleted"
    ):
        dcnm_vpc_pair.dcnm_vpc_pair_get_want()
        dcnm_vpc_pair.dcnm_vpc_pair_get_have()

        # self.want would have defaulted all optional objects not included in playbook. But the way
        # these objects are handled is different between 'merged' and 'replaced' states. For 'merged'
        # state, objects not included in the playbook must be left as they are and for state 'replaced'
        # they must be purged or defaulted.

        dcnm_vpc_pair.dcnm_vpc_pair_update_want()

    if (module.params["state"] == "merged") or (
        module.params["state"] == "replaced"
    ):
        dcnm_vpc_pair.dcnm_vpc_pair_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_vpc_pair.dcnm_vpc_pair_get_diff_deleted()

    if module.params["state"] == "overridden":
        dcnm_vpc_pair.dcnm_vpc_pair_get_diff_overridden(dcnm_vpc_pair.config)

    if module.params["state"] == "query":
        dcnm_vpc_pair.dcnm_vpc_pair_get_diff_query()

    dcnm_vpc_pair.result["diff"] = dcnm_vpc_pair.changed_dict

    dcnm_vpc_pair.changed_dict[0]["debugs"].append(
        {"Managable": dcnm_vpc_pair.managable}
    )
    dcnm_vpc_pair.changed_dict[0]["debugs"].append(
        {"Monitoring": dcnm_vpc_pair.monitoring}
    )

    dcnm_vpc_pair.changed_dict[0]["debugs"].append(
        {"Meta_Switches": dcnm_vpc_pair.meta_switches}
    )

    if dcnm_vpc_pair.diff_create or dcnm_vpc_pair.diff_delete:
        dcnm_vpc_pair.result["changed"] = True

    if module.check_mode:
        dcnm_vpc_pair.result["changed"] = False
        module.exit_json(**dcnm_vpc_pair.result)

    dcnm_vpc_pair.dcnm_vpc_pair_send_message_to_dcnm()

    module.exit_json(**dcnm_vpc_pair.result)


if __name__ == "__main__":
    main()
