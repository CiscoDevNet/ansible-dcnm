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
__author__ = "Mallik Mudigonda"

DOCUMENTATION = """
---
module: dcnm_sgrp
short_description: DCNM Ansible Module for managing Security Groups.
version_added: "3.5.0"
description:
    - "DCNM Ansible Module for managing Security Groups."
author: Mallik Mudigonda(@mmudigon)
options:
  fabric:
    description:
      - Name of the target fabric for Security Group operations
    type: str
    required: true
  state:
    description:
      - The required state of the configuration after module completion.
    type: str
    choices: ['merged', 'replaced', 'overridden', 'deleted', 'query']
    default: merged
  deploy:
    description:
      - Flag indicating if the configuration must be pushed to the switch.
      - A value of 'none' will not push the changes to the controller. A value
        of 'switches' will perform switch level deploy for the changes made.
    type: str
    choices: ["none", "switches"]
    default: switches
  config:
    description:
      - A list of dictionaries containing Security Group information
    type: list
    elements: dict
    default: []
    suboptions:
      group_name:
        description:
          - Name of the Security Group.
          - This argument must have a minimum length of 1 and a maximum length of 63.
        required: true
        type: str
      group_id:
        description:
          - A unique identifier to identify the group. This argument is optional and will be allocated by
            the module before a payload is pushed to the controller. If this argument is included in the input,
            then the user provided argument is used.
          - This argument takes a minimum value of 16 and a maximum value of 65535.
        type: int
      ip_selectors:
        description:
          - A list of dictionaries containing Security Group IP Selector information.
        type: list
        elements: dict
        default: []
        suboptions:
          type:
            description:
              - Specifies the type of IP selector.
            type: str
            choices: ["Connected Endpoints", "External Subnets"]
            required: true
          vrf_name:
            description:
              - VRF name associated with the IP prefixes.
              - This argument must have a minimum length of 1 and a maximum length of 32.
            type: str
            required: true
          ip:
            description:
              - IP address and mask.
            type: str
            required: true
      network_selectors:
        description:
          - A list of dictionaries containing Security Group Network Selector information.
        type: list
        elements: dict
        default: []
        suboptions:
          vrf_name:
            description:
              - VRF name.
              - This argument must have a minimum length of 1 and a maximum length of 32.
            type: str
            required: true
          network:
            description:
              - Network name.
              - This argument must have a minimum length of 1 and a maximum length of 32.
            type: str
            required: true
"""

EXAMPLES = """

# States:
# This module supports the following states:
#
# Merged:
#   Security Groups defined in the playbook will be merged into the target fabric.
#
#   The Security Groups listed in the playbook will be created if not already present on the DCNM
#   server. If the Security Group is already present and the configuration information included
#   in the playbook is either different or not present in DCNM, then the corresponding
#   information is added to the DCNM. If a Security Group  mentioned in playbook
#   is already present on DCNM and there is no difference in configuration, no operation
#   will be performed for such groups.
#
# Replaced:
#   Security Groups defined in the playbook will be replaced in the target fabric.
#
#   The state of the Security Groups listed in the playbook will serve as source of truth for the
#   same Security Groups present on the DCNM under the fabric mentioned. Additions and updations
#   will be done to bring the DCNM Security Groups to the state listed in the playbook.
#   Note: Replace will only work on the Security Groups mentioned in the playbook.
#
# Overridden:
#   Security Groups defined in the playbook will be overridden in the target fabric.
#
#   The state of the Security Groups listed in the playbook will serve as source of truth for all
#   the Security Groups under the fabric mentioned. Additions and deletions will be done to bring
#   the DCNM Security Groups to the state listed in the playbook. All Security Groups other than the
#   ones mentioned in the playbook will be deleted.
#   Note: Override will work on the all the Security Groups present in the DCNM Fabric.
#
# Deleted:
#   Security Groups defined in the playbook will be deleted in the target fabric.
#
#   Deletes the list of Security Groups specified in the playbook.  If the playbook does not include
#   any Security Group information, then all Security Groups from the fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the Security Groups listed in the playbook.

# CREATE SECURITY GROUPS

- name: Create Security Groups
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    deploy: switches                                    # choose from ["none", "switches"]
    state: merged                                       # choose form [merged, replaced, deleted, overridden, query]
    config:
      - group_name: LSG_15001
        group_id: 15001                                 # choose between [min:16, max:65535]
        ip_selectors:
          - type: "Connected Endpoints"
            vrf_name: MyVRF_50001
            ip: 11.1.1.1/24
          - type: "External Subnets"
            vrf_name: MyVRF_50001
            ip: 2001::01/64
          - type: "Connected Endpoints"
            vrf_name: MyVRF_50001
            ip: 11.3.3.1/24
        network_selectors:
          - vrf_name: MyVRF_50001
            network: MyNetwork_30001
        switch:
          - 192.168.1.1
  register: result

# DELETE SECURITY GROUPS

- name: Delete all the security groups from the fabric
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    state: deleted                     # choose form [merged, replaced, deleted, overridden, query]
    deploy: switches                   # choose from ["none", "switches"]
  register: result

- name: Delete security groups by ID
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    state: deleted                     # choose from [merged, replaced, deleted, overridden, query]
    deploy: switches                   # choose from ["none", "switches"]
    config:
      - group_id: 15001
  register: result

- name: Delete security groups by Name
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    state: deleted                     # choose from [merged, replaced, deleted, overridden, query]
    deploy: switches                   # choose from ["none", "switches"]
    config:
      - group_name: LSG_15001
  register: result

- name: Delete security groups by Name and ID
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    state: deleted                     # choose from [merged, replaced, deleted, overridden, query]
    deploy: switches                   # choose from ["none", "switches"]
    config:
      - group_name: LSG_15001
        group_id: 15001
  register: result

# REPLACE SECURITY GROUPS

- name: Replace Security Groups
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    deploy: switches                                    # choose from ["none", "switches"]
    state: replaced                                     # choose from [merged, replaced, deleted, overridden, query]
    config:
      - group_name: "LSG_15001"
        group_id: 15001                                 # choose between [min:16, max:65535]
        ip_selectors:
          - type: "Connected Endpoints"
            vrf_name: MyVRF_50003
            ip: 21.1.1.1/24
          - type: "Connected Endpoints"
            vrf_name: MyVRF_50003
            ip: 3001::01/64
          - type: "External Subnets"
            vrf_name: MyVRF_50003
            ip: 11.3.3.1/24
        network_selectors:
          - vrf_name: MyVRF_50003
            network: MyNetwork_30003
        switch:
          - 912.168.1.1
  register: result

# OVERRIDE SECURITY GROUPS

- name: Override Security Groups - delete all existing groups
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    deploy: switches                                    # choose from ["none", "switches"]
    state: overridden                                   # choose from [merged, replaced, deleted, overridden, query]
  register: result

- name: Override Security Groups - delete all except the one included
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    deploy: switches                                    # choose from ["none", "switches"]
    state: overridden                                   # choose from [merged, replaced, deleted, overridden, query]
    config:
      - group_name: "LSG_15001"
        group_id: 15001                                 # choose between [min:16, max:65535]
        ip_selectors:
          - type: "Connected Endpoints"
            vrf_name: MyVRF_50001
            ip: 11.1.1.1/24
          - type: "Connected Endpoints"
            vrf_name: MyVRF_50001
            ip: 2001::01/64
          - type: "Connected Endpoints"
            vrf_name: MyVRF_50001
            ip: 11.3.3.1/24
        network_selectors:
          - vrf_name: MyVRF_50001
            network: MyNetwork_30001
        switch:
          - 192.168.1.1
  register: result

# QUERY SECURITY GROUPS

- name: Query Security Groups - no filters
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    deploy: none                                        # choose from ["none", "switches"]
    state: query
  register: result

- name: Query Security Groups - with  IDs
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    config:
      - group_id: 15001                                 # 16 - 65535
      - group_id: 15002                                 # 16 - 65535
      - group_id: 15003
      - group_id: 15004
    deploy: none                                        # choose from ["none", "switches"]
    state: query
  register: result

- name: Query Security Groups - with names
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    config:
      - group_name: "LSG_15001"
      - group_name: "LSG_15002"
      - group_name: "LSG_15003"
      - group_name: "LSG_15004"
    deploy: none                                        # choose from ["none", "switches"]
    state: query
  register: result

- name: Q._verbosityuery Security Groups - with names and IDs
  cisco.dcnm.dcnm_sgrp:
    fabric: test-fabric
    config:
      - group_name: "LSG_15001"
        group_id: 15001                                 # 16 - 65535
      - group_name: "LSG_15002"
        group_id: 15002                                 # 16 - 65535
      - group_name: "LSG_15003"
        group_id: 15003                                 # 16 - 65535
      - group_name: "LSG_15004"
        group_id: 15004                                 # 16 - 65535
    deploy: none                                        # choose from ["none", "switches"]
    state: query
  register: result
"""

import copy
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import (
    ResponseHandler,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import (
    RestSend,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import (
    Sender,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.common.common_utils import (
    Version,
    InventoryData,
    FabricInfo,
    SwitchInfo,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    validate_list_of_dicts,
    dcnm_get_ip_addr_info,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_sgrp_utils import (
    Paths,
    dcnm_sgrp_utils_check_if_meta,
    dcnm_sgrp_utils_get_sgrp_info,
    dcnm_sgrp_utils_get_sgrp_payload,
    dcnm_sgrp_utils_update_sgrp_information,
    dcnm_sgrp_utils_validate_profile,
    dcnm_sgrp_utils_get_matching_have,
    dcnm_sgrp_utils_get_matching_cfg,
    dcnm_sgrp_utils_merge_want_and_have,
    dcnm_sgrp_utils_compare_want_and_have,
    dcnm_sgrp_utils_get_sgrp_deploy_payload,
    dcnm_sgrp_utils_process_delete_payloads,
    dcnm_sgrp_utils_process_create_payloads,
    dcnm_sgrp_utils_process_modify_payloads,
    dcnm_sgrp_utils_process_deploy_payloads,
    dcnm_sgrp_utils_update_deploy_info,
    dcnm_sgrp_utils_get_delete_payload,
    dcnm_sgrp_utils_translate_sgrp_info,
    dcnm_sgrp_utils_get_sync_status,
    dcnm_sgrp_utils_get_delete_list,
    dcnm_sgrp_utils_get_all_filtered_sgrp_objects,
    dcnm_sgrp_utils_validate_devices,
)

#
# WARNING:
#   This file is automatically generated. Take a backup of your changes to this file before
#   manually running cg_run.py script to generate it again
#


# Resource Class object which includes all the required methods and data to configure and maintain Security Groups.
class DcnmSgrp:
    def __init__(self, module):

        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.deploy = module.params["deploy"]
        self.config = copy.deepcopy(module.params.get("config", []))
        self.sync_info = {}
        self.sgrp_info = []
        self.sgrp_list = []
        self.want = []
        self.have = []
        self.diff_create = [{"bulk": [], "individual": []}]
        self.diff_modify = [{"bulk": [], "individual": []}]
        self.diff_delete = []
        self.diff_deploy = {}
        self.diff_delete_deploy = {}
        self.monitoring = []
        self.meta_switches = []
        self.changed_dict = [
            {
                "merged": [],
                "deleted": [],
                "delete_deploy": [],
                "modified": [],
                "query": [],
                "deploy": {},
                "debugs": [],
            }
        ]

        self.result = dict(changed=False, diff=[], response=[])

    def dcnm_sgrp_merge_want_and_have_objects(self, want, have):

        """
        Routine to merge the 'want' and 'have' if required. If an object requires mering, then the
        values from 'want' and 'have' will be combined into one instead of overwriting.

        Parameters:
            want (dict): Object to be updated with information from have
            have (dict): Existing Security Group information

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
                    dcnm_sgrp_utils_merge_want_and_have(self, want, have, key)
                # Remove the <key>_defaulted from want
                want.pop(key + "_defaulted")

    def dcnm_sgrp_merge_want_and_have(self, want, have):

        """
        Routine to check for mergeable keys in want and merge the same with whatever is already exsiting
        in have.

        Parameters:
            want (dict): Object to be updated with information from have
            have (dict): Existing Security Group information

        Returns:
            None
        """

        defaulted_keys = []

        # Code is generated for comparing "nvPairs" objects alone. If there are other nested structures
        # in the want and have objects that need to be compared, add the necessary code here.

        # There may be certain objects like "Freeform config" in the parameters which
        # inlcude a list of commands or parameters like member ports which inlcudes a
        # list of interfaces. During MERGE, the values from WANT should be merged
        # to values in have. Identify the actual keys in WANT and HAVE and update the
        # below block of CODE to achieve the merge

        self.dcnm_sgrp_merge_want_and_have_objects(want, have)

    def dcnm_sgrp_get_diff_query(self):

        """
        Routine to retrieve Security Group from controller. This routine extracts information provided by the
        user and filters the output based on that.

        Parameters:
            None

        Returns:
            None
        """

        sgrp_list = dcnm_sgrp_utils_get_all_filtered_sgrp_objects(self)
        if sgrp_list != []:
            self.result["response"].extend(sgrp_list)

    def dcnm_sgrp_get_diff_overridden(self, cfg):

        """
        Routine to override existing Security Group information with what is included in the playbook. This routine
        deletes all Security Group objects which are not part of the current config and creates new ones based on what is
        included in the playbook

        Parameters:
            cfg (dct): Configuration information from playbook

        Returns:
            None
        """

        # First get list of all objects that exist. Ignore security group objects whose groupTypd is "defaultgroup" since
        # they cannot be deleted.
        del_list = dcnm_sgrp_utils_get_delete_list(self)

        # 'del_list' contains all Security Group information in 'have' format. Use that to update delete and delete
        # deploy payloads

        for elem in del_list:
            self.dcnm_sgrp_update_delete_payloads(elem)

        if cfg == []:
            return

        if self.want:
            # New configuration is included. Delete all existing Security Group objects and create new objects as requested
            # through the configuration
            self.dcnm_sgrp_get_diff_merge()

    def dcnm_sgrp_get_diff_deleted(self):

        """
        Routine to get a list of payload information that will be used to delete Sgrp.
        This routine updates self.diff_delete with payloads that are used to delete Sgrp
        from the server.

        Parameters:
            None

        Returns:
            None
        """

        if self.sgrp_info == []:
            # User has not included any config. Delete all existing Security Group objects from DCNM
            self.dcnm_sgrp_get_diff_overridden([])
            return

        for elem in self.sgrp_info:

            xelem = dcnm_sgrp_utils_translate_sgrp_info(self, elem)
            have = dcnm_sgrp_utils_get_sgrp_info(self, xelem)

            if have != []:
                if elem.get("switch", None) is not None:
                    have["switch"] = elem["switch"]
                self.dcnm_sgrp_update_delete_payloads(have)

    def dcnm_sgrp_update_delete_payloads(self, have):

        # Get the delete payload based on 'have'
        del_payload = dcnm_sgrp_utils_get_delete_payload(self, have)

        if del_payload not in self.diff_delete:
            self.changed_dict[0]["deleted"].append(del_payload)
            self.diff_delete.append(del_payload)

            if self.deploy != "none":
                # A delete of security group information must be followed by deploy to clean up VRFs and Networks.
                dcnm_sgrp_utils_update_deploy_info(
                    self, have, self.diff_delete_deploy
                )
                self.changed_dict[0]["delete_deploy"] = copy.deepcopy(
                    self.diff_delete_deploy
                )

    def dcnm_sgrp_get_diff_merge(self):

        """
        Routine to populate a list of payload information in self.diff_create to create/update Sgrp.

        Parameters:
            None

        Returns:
            None
        """

        for elem in self.want:
            groupId = elem.get("groupId", 0)
            if groupId == 0:
                bulk = False
            else:
                bulk = True

            rc, reasons, have = dcnm_sgrp_utils_compare_want_and_have(
                self, elem
            )

            msg = f"Compare Want and Have: Return Code = {rc}, Reasons = {reasons}, Have = {have}\n"
            self.log.info(msg)

            if rc == "DCNM_SGRP_CREATE":
                # Object does not exists, create a new one. Security groups which include groupIds can be created in bulk.
                # For groups that doesn't include groupId, they must be created individually by allocating groupIds.
                if bulk:
                    if elem not in self.diff_create[0]["bulk"]:
                        self.changed_dict[0]["merged"].append(elem)
                        self.diff_create[0]["bulk"].append(elem)
                else:
                    if elem not in self.diff_create[0]["individual"]:
                        self.changed_dict[0]["merged"].append(elem)
                        self.diff_create[0]["individual"].append(elem)
            if rc == "DCNM_SGRP_MERGE":
                # Object already exists, and needs an update
                # Fields like CONF which are a list of commands should be handled differently in this case.
                # For existing objects, we will have to merge the current list of commands with already existing
                # ones in have. For replace, no need to merge them. They must be replaced with what is given.
                if self.module.params["state"] == "merged":
                    self.dcnm_sgrp_merge_want_and_have(elem, have)

                if elem not in self.diff_modify[0]["individual"]:
                    self.changed_dict[0]["modified"].append(elem)
                    self.changed_dict[0]["debugs"].append({"REASONS": reasons})
                    self.diff_modify[0]["individual"].append(elem)

            # Check if "deploy" flag is set to a valid value. If yes, deploy the changes.
            if self.deploy != "none":
                # Before building deploy payload, check
                #  - if something is being created
                #  - if something that is existing is being updated
                #  - if switches are in "In-Sync" state already

                if self.sync_info == {}:
                    self.sync_info = dcnm_sgrp_utils_get_sync_status(self)

                dcnm_sgrp_utils_get_sgrp_deploy_payload(self, elem, rc)

        if self.diff_deploy != {}:
            self.changed_dict[0]["deploy"] = copy.deepcopy(self.diff_deploy)

    def dcnm_sgrp_update_want(self):

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

            match_have = dcnm_sgrp_utils_get_matching_have(self, want)

            if match_have != []:
                match_cfg = dcnm_sgrp_utils_get_matching_cfg(self, want)

                if match_cfg == []:
                    continue

            for melem in match_have:
                dcnm_sgrp_utils_update_sgrp_information(
                    self, want, melem, match_cfg[0]
                )

    def dcnm_sgrp_get_want(self):

        """
        This routine updates self.want with the payload information based on the playbook configuration.

        Parameters:
            None

        Returns:
            None
        """

        if self.config == []:
            return

        for elem in self.sgrp_info:

            # If a separate payload is required for every switch included in the payload, then modify this
            # code to loop over the switches. Also the get payload routine should be modified appropriately.
            # Security groups are created independent of devices. The same payload is deployed to each switch.
            # So no need to create a seperate payload for each switch.

            payload = self.dcnm_sgrp_get_payload(elem)

            if payload not in self.want:
                self.want.append(payload)

    def dcnm_sgrp_get_have(self):

        """
        Routine to get exisitng sgrp information from DCNM that matches information in self.want.
        This routine updates self.have with all the sgrp that match the given playbook configuration

        Parameters:
            None

        Returns:
            None
        """

        if self.want == []:
            return

        for elem in self.want:
            have = dcnm_sgrp_utils_get_sgrp_info(self, elem)
            if (have != []) and (have not in self.have):
                # If the given object already exist, update the group id here
                elem["groupId"] = have["groupId"]
                self.have.append(have)

    def dcnm_sgrp_validate_deleted_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        deleted state input. This routine updates self.sgrp_info with
        validated playbook information related to deleted state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {
            "group_name": {"type": "str"},
            "group_id": {"type": "int"},
            "switch": {"type": "list", "elements": "str"},
        }

        sgrp_info, invalid_params = validate_list_of_dicts(cfg, arg_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if sgrp_info:
            self.sgrp_info.extend(sgrp_info)

    def dcnm_sgrp_validate_query_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        query state input. This routine updates self.sgrp_info with
        validated playbook information related to query state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {"group_name": {"type": "str"}, "group_id": {"type": "int"}}

        sgrp_info, invalid_params = validate_list_of_dicts(cfg, arg_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if sgrp_info:
            self.sgrp_info.extend(sgrp_info)

    def dcnm_sgrp_validate_input(self, cfg):

        # The generator hanldes only the case where:
        #   - there are some common paremeters that are included in the playbook
        #   - and a profile which is a 'dict' and which is either based on a template or some fixed structure
        # NOTE: This code assumes that the nested structure will be under a key called 'profile'. If not modify the
        #       same appropriately.
        # This routine generates code to validate the common part and the 'profile' part which is one level nested.
        # Users must modify this code appropriately to hanlde any further nested structures that may be part
        # of playbook input.

        common_spec = {
            "group_name": {"required": "True", "type": "str"},
            "group_id": {"type": "int", "default": 0},
            "ip_selectors": {"type": "list", "default": []},
            "network_selectors": {"type": "list", "default": []},
            "switch": {"required": "True", "type": "list", "elements": "str"},
        }
        ip_selectors_spec = {
            "type": {
                "required": "True",
                "type": "str",
                "choices": ["Connected Endpoints", "External Subnets"],
            },
            "vrf_name": {"required": "True", "type": "str"},
            "ip": {"required": "True", "type": "str"},
        }
        network_selectors_spec = {
            "vrf_name": {"required": "True", "type": "str"},
            "network": {"required": "True", "type": "str"},
        }

        sgrp_info, invalid_params = validate_list_of_dicts(cfg, common_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if cfg[0].get("ip_selectors", None) is not None:
            sgrp_ips_info = dcnm_sgrp_utils_validate_profile(
                self, cfg[0]["ip_selectors"], ip_selectors_spec
            )
            if sgrp_ips_info:
                sgrp_info[0]["ip_selectors"][0].update(sgrp_ips_info[0])

        if cfg[0].get("network_selectors", None) is not None:
            sgrp_nets_info = dcnm_sgrp_utils_validate_profile(
                self, cfg[0]["network_selectors"], network_selectors_spec
            )
            if sgrp_nets_info:
                sgrp_info[0]["network_selectors"][0].update(sgrp_nets_info[0])

        self.sgrp_info.append(sgrp_info[0])

    def dcnm_sgrp_validate_all_input(self):

        """
        Routine to validate playbook input based on the state. Since each state has a different
        config structure, this routine handles the validation based on the given state

        Parameters:
            None

        Returns:
            None
        """

        if [] is self.config:
            return

        cfg = []
        for item in self.config:

            citem = copy.deepcopy(item)

            cfg.append(citem)

            if self.module.params["state"] == "query":
                # config for query state is different. So validate query state differently
                self.dcnm_sgrp_validate_query_state_input(cfg)
            elif self.module.params["state"] == "deleted":
                # config for deleted state is different. So validate deleted state differently
                self.dcnm_sgrp_validate_deleted_state_input(cfg)
            else:
                self.dcnm_sgrp_validate_input(cfg)
            cfg.remove(citem)

    def dcnm_sgrp_get_payload(self, sgrp_info):

        """
        This routine builds the complete object payload based on the information in self.want

        Parameters:
            sgrp_info (dict): Object information

        Returns:
            sgrp_payload (dict): Object payload information populated with appropriate data from playbook config
        """

        sgrp_payload = dcnm_sgrp_utils_get_sgrp_payload(self, sgrp_info)

        return sgrp_payload

    def dcnm_sgrp_update_switch_info(self):

        """
        Routine to update inventory data for all fabrics included in the playbook. This routine
        also updates ip_sn, sn_hn and hn_sn objetcs from the updated inventory data.

        Parameters:
            None

        Returns:
            None
        """

        try:
            switch_info = SwitchInfo()
            switch_info.inventory_data = self.inventory_data
            switch_info.fabric = self.fabric
            switch_info.commit()
        except ValueError as error:
            self.module.fail_json(msg=f"{str(error)}")

        self.managable = switch_info.managable
        self.meta_switches = switch_info.meta_switches
        self.ip_sn = switch_info.ip_sn
        self.hn_sn = switch_info.hn_sn
        self.sn_hn = switch_info.sn_hn
        self.sn_ip = switch_info.sn_ip

    def dcnm_sgrp_translate_playbook_info(self, config, ip_sn, hn_sn):

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

        if [] is config:
            return

        for cfg in config:
            index = 0
            if cfg.get("switch", None) is None:
                continue
            for sw_elem in cfg["switch"][:]:
                if dcnm_sgrp_utils_check_if_meta(self, sw_elem) is True:
                    continue
                if sw_elem in self.ip_sn or sw_elem in self.hn_sn:
                    addr_info = dcnm_get_ip_addr_info(
                        self.module, sw_elem, ip_sn, hn_sn
                    )
                    cfg["switch"][index] = addr_info
                else:
                    cfg["switch"].remove(sw_elem)
                index = index + 1

            if cfg.get("switch", None) is not None:
                # Check if the switches included in the config are Manageable.
                dcnm_sgrp_utils_validate_devices(self, cfg)

    def dcnm_sgrp_send_message_to_dcnm(self):

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

        delete_flag = dcnm_sgrp_utils_process_delete_payloads(self)
        create_flag = dcnm_sgrp_utils_process_create_payloads(self)
        modify_flag = dcnm_sgrp_utils_process_modify_payloads(self)
        deploy_flag = dcnm_sgrp_utils_process_deploy_payloads(
            self, self.diff_deploy
        )

        msg = f"Flags: CR = {create_flag}, DL = {delete_flag}, MO = {modify_flag}, DP = {deploy_flag}\n"
        self.log.debug(msg)

        self.result["changed"] = (
            create_flag or modify_flag or delete_flag or deploy_flag
        )

    def dcnm_sgrp_update_module_info(self):

        """
        Routine to update version and fabric details

        Parameters:
            None

        Returns:
            None
        """

        try:
            version = Version()
            version.module = self.module
            version.commit()
            self.dcnm_version = version.dcnm_version
        except ValueError as error:
            self.module.fail_json(msg=f"{str(error)}")

        try:
            inv_data = InventoryData()
            inv_data.module = self.module
            inv_data.fabric = self.fabric
            inv_data.commit()
            self.inventory_data = inv_data.inventory_data
        except ValueError as error:
            self.module.fail_json(msg=f"{str(error)}")

        try:
            paths = Paths()
            paths.version = self.dcnm_version
            paths.commit()
            self.paths = paths.paths
        except ValueError as error:
            self.module.fail_json(msg=f"{str(error)}")

        try:
            fabric_info = FabricInfo()
            fabric_info.module = self.module
            fabric_info.fabric = self.fabric
            fabric_info.rest_send = self.rest_send
            fabric_info.paths = self.paths
            fabric_info.commit()
        except ValueError as error:
            self.module.fail_json(msg=f"{str(error)}")


def main():

    """ main entry point for module execution
    """
    element_spec = dict(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict", default=[]),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "replaced", "overridden", "query"],
        ),
        deploy=dict(
            type="str", default="switches", choices=["switches", "none"]
        ),
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    dcnm_sgrp = DcnmSgrp(module)

    state = module.params["state"]

    # Initialize the logger
    try:
        # Set the following to True if logging is required
        enable_logging = True
        logger = Log(module)

        if enable_logging is True:
            collection_path = "/Users/mmudigon/Desktop/Ansible/collections/ansible_collections/cisco/dcnm"
            config_file = f"{collection_path}/plugins/module_utils/common/logging_config.json"
            logger.config = config_file
        logger.commit()
    except ValueError as error:
        module.fail_json(msg=str(error))

    msg = f"######################### BEGIN STATE = {state} ##########################\n"
    dcnm_sgrp.log.debug(msg)

    # Initialize the Sender object
    sender = Sender()
    sender.ansible_module = module
    dcnm_sgrp.rest_send = RestSend(module.params)
    dcnm_sgrp.rest_send.response_handler = ResponseHandler()
    dcnm_sgrp.rest_send.sender = sender

    # Fill up the version and fabric related details
    dcnm_sgrp.dcnm_sgrp_update_module_info()

    if [] is dcnm_sgrp.config:
        if state == "merged" or state == "replaced":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_sgrp.config
                )
            )

    dcnm_sgrp.dcnm_sgrp_update_switch_info()

    dcnm_sgrp.dcnm_sgrp_translate_playbook_info(
        dcnm_sgrp.config, dcnm_sgrp.ip_sn, dcnm_sgrp.hn_sn
    )
    dcnm_sgrp.dcnm_sgrp_validate_all_input()

    msg = f"Config Info = {dcnm_sgrp.config}\n"
    dcnm_sgrp.log.info(msg)

    msg = f"Validated Security Group Association Info = {dcnm_sgrp.sgrp_info}\n"
    dcnm_sgrp.log.info(msg)

    if (
        module.params["state"] != "query"
        and module.params["state"] != "deleted"
    ):
        dcnm_sgrp.dcnm_sgrp_get_want()

        msg = f"Want = {dcnm_sgrp.want}\n"
        dcnm_sgrp.log.info(msg)

        dcnm_sgrp.dcnm_sgrp_get_have()

        msg = f"Have = {dcnm_sgrp.have}\n"
        dcnm_sgrp.log.info(msg)

        # self.want would have defaulted all optional objects not included in playbook. But the way
        # these objects are handled is different between 'merged' and 'replaced' states. For 'merged'
        # state, objects not included in the playbook must be left as they are and for state 'replaced'
        # they must be purged or defaulted.

        dcnm_sgrp.dcnm_sgrp_update_want()
        msg = f"Updated Want = {dcnm_sgrp.want}\n"
        dcnm_sgrp.log.info(msg)

    if (module.params["state"] == "merged") or (
        module.params["state"] == "replaced"
    ):
        dcnm_sgrp.dcnm_sgrp_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_sgrp.dcnm_sgrp_get_diff_deleted()

    if module.params["state"] == "overridden":
        dcnm_sgrp.dcnm_sgrp_get_diff_overridden(dcnm_sgrp.config)

    if module.params["state"] == "query":
        dcnm_sgrp.dcnm_sgrp_get_diff_query()

    msg = f"Create Info = {dcnm_sgrp.diff_create}\n"
    dcnm_sgrp.log.info(msg)

    msg = f"Replace Info = {dcnm_sgrp.diff_modify}\n"
    dcnm_sgrp.log.info(msg)

    msg = f"Delete Info = {dcnm_sgrp.diff_delete}\n"
    dcnm_sgrp.log.info(msg)

    msg = f"Deploy Info = {dcnm_sgrp.diff_deploy}\n"
    dcnm_sgrp.log.info(msg)

    msg = f"Delete Deploy Info = {dcnm_sgrp.diff_delete_deploy}\n"
    dcnm_sgrp.log.info(msg)

    dcnm_sgrp.result["diff"] = dcnm_sgrp.changed_dict
    dcnm_sgrp.changed_dict[0]["debugs"].append(
        {"Managable": dcnm_sgrp.managable}
    )
    dcnm_sgrp.changed_dict[0]["debugs"].append(
        {"Monitoring": dcnm_sgrp.monitoring}
    )

    dcnm_sgrp.changed_dict[0]["debugs"].append(
        {"Meta_Switches": dcnm_sgrp.meta_switches}
    )

    if (
        (dcnm_sgrp.diff_create[0]["bulk"])
        or (dcnm_sgrp.diff_create[0]["individual"])
        or (dcnm_sgrp.diff_modify[0]["bulk"])
        or (dcnm_sgrp.diff_modify[0]["individual"])
        or (dcnm_sgrp.diff_delete)
        or (dcnm_sgrp.diff_deploy)
    ):
        dcnm_sgrp.result["changed"] = True

    if module.check_mode:
        dcnm_sgrp.result["changed"] = False
        module.exit_json(**dcnm_sgrp.result)

    dcnm_sgrp.dcnm_sgrp_send_message_to_dcnm()

    msg = f"######################### END STATE = {state} ##########################\n"
    dcnm_sgrp.log.debug(msg)

    module.exit_json(**dcnm_sgrp.result)


if __name__ == "__main__":
    main()
