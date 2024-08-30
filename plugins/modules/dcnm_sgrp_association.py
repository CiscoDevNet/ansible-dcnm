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
module: dcnm_sgrp_association
short_description: DCNM Ansible Module for managing Security Groups Associatons.
version_added: "3.5.0"
description:
    - "DCNM Ansible Module for managing Security Groups Associations."
author: Mallik Mudigonda(@mmudigon)
options:
  fabric:
    description:
      - Name of the target fabric for Security Group Association operations
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
      src_group_name:
        description:
          - Name of the source Security Group in the association.
          - This argument must have a minimum length of 1 and a maximum length of 63.
        required: true
        type: str
      src_group_id:
        description:
          - A unique identifier to identify the source group. This argument is optional and will be allocated by
            the module before a payload is pushed to the controller. If this argument is included in the input,
            then the user provided argument is used.
          - This argument takes a minimum value of 16 and a maximum value of 65535.
        type: int
      dst_group_name:
        description:
          - Name of the destination Security Group in the association.
          - This argument must have a minimum length of 1 and a maximum length of 63.
        required: true
        type: str
      dst_group_id:
        description:
          - A unique identifier to identify the destination group. This argument is optional and will be allocated by
            the module before a payload is pushed to the controller. If this argument is included in the input,
            then the user provided argument is used.
          - This argument takes a minimum value of 16 and a maximum value of 65535.
        type: int
      vrf_name:
        description:
          - VRF name associated with the Security Group Association.
          - This argument must have a minimum length of 1 and a maximum length of 32.
        type: str
        required: true
      contract_name:
        description:
          - Contract name associated with the Security Group Association.
        type: str
        required: true
      switch:
        description:
        - IP address or DNS name of the management interface. All switches mentioned in this list
          will be deployed with the included configuration.
        type: list
        elements: str
        required: true
"""

EXAMPLES = """

# States:
# This module supports the following states:
#
# Merged:
#   Security Group Associations defined in the playbook will be merged into the target fabric.
#
#   The Security Group Associations listed in the playbook will be created if not already present on the DCNM
#   server. If the Security Group Association is already present and the configuration information included
#   in the playbook is either different or not present in DCNM, then the corresponding
#   information is added to the DCNM. If a Security Group Asssociation  mentioned in playbook
#   is already present on DCNM and there is no difference in configuration, no operation
#   will be performed for such groups.
#
# Replaced:
#   Security Group Associations defined in the playbook will be replaced in the target fabric.
#
#   The state of the Security Group Associations listed in the playbook will serve as source of truth for the
#   same Security Group Associations present on the DCNM under the fabric mentioned. Additions and updations
#   will be done to bring the DCNM Security Group Associations to the state listed in the playbook.
#   Note: Replace will only work on the Security Group Associations mentioned in the playbook.
#
# Overridden:
#   Security Group Associations defined in the playbook will be overridden in the target fabric.
#
#   The state of the Security Group Associations listed in the playbook will serve as source of truth for all
#   the Security Group Associations under the fabric mentioned. Additions and deletions will be done to bring
#   the DCNM Security Group Associations to the state listed in the playbook. All Security Group Associations other than the
#   ones mentioned in the playbook will be deleted.
#   Note: Override will work on the all the Security Group Associations present in the DCNM Fabric.
#
# Deleted:
#   Security Group Associations defined in the playbook will be deleted in the target fabric.
#
#   Deletes the list of Security Group Associations specified in the playbook.  If the playbook does not include
#   any Security Group Association information, then all Security Group Associations from the fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the Security Group Associations listed in the playbook.

# CREATE SECURITY GROUP ASSOCIATIONS

- name: Create Security Group Associations - with and without mentioning group IDs
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    deploy: switches                                    # choose from ["none", "switches"]
    state: merged                                       # choose from [merged, replaced, deleted, overridden, query]
    config:
      - src_group_name: "LSG_15001"
        dst_group_name: "LSG_15001"
        src_group_id: 15001                             # Group Id associated with src_group_name
        dst_group_id: 15001                             # Group Id associated with dst_group_name
        vrf_name: "MyVRF_50001"
        contract_name: CONTRACT1
        switch:
          - 192.168.1.1
          - 192.168.1.2

      - src_group_name: "LSG_15002"
        dst_group_name: "LSG_15002"
        vrf_name: "MyVRF_50002"
        contract_name: CONTRACT1
        switch:
          - 192.168.1.1
          - 192.168.1.2

# DELETE SECURITY GROUP ASSOCIATIONS

- name: Delete Security Group Associations - without config
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
    deploy: switches                    # choose from ["none", "switches"]

- name: Delete Security Group Associations - with group name
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
    deploy: switches                    # choose from ["none", "switches"]
    config:
      - src_group_name: "LSG_15001"
        switch:
          - 192.168.1.1

- name: Delete Security Group Associations - with group Id
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
    deploy: switches                    # choose from ["none", "switches"]
    config:
      - dst_group_id: 15001

- name: Delete Security Group Associations - with vrf name
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
    deploy: switches                    # choose from ["none", "switches"]
    config:
      - vrf_name: "MyVRF_50003"
        switch:
          - 192.168.1.2

- name: Delete Security Group Associations - with contract name
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
    deploy: switches                    # choose from ["none", "switches"]
    config:
      - contract_name: "CONTRACT1"

- name: Delete Security Group Associations - sepcifying all
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
    deploy: switches                    # choose from ["none", "switches"]
    config:
      - src_group_id: 15001
        dst_group_id: 15002
        src_group_name: "LSG_15001"
        dst_group_name: "LSG_15002"
        vrf_name: "MyVRF_50003"
        contract_name: "CONTRACT1"

# REPLACE SECURITY GROUP ASSOCIATIONS

- name: Replace Security Group Associations
  cisco.dcnm.dcnm_sgrp_association:
    fabric: "{{ ansible_it_fabric }}"
    deploy: switches                                    # choose from ["none", "switches"]
    state: replaced                                     # choose from [merged, replaced, deleted, overridden, query]
    config:
      - src_group_name: "LSG_15001"
        dst_group_name: "LSG_15001"
        src_group_id: 15001                             # Group Id associated with src_group_name
        dst_group_id: 15001                             # Group Id associated with dst_group_name
        vrf_name: "MyVRF_50001"
        contract_name: ICMP-PERMIT
        switch:
          - 192.168.1.1
          - 192.168.1.2

# OVERRIDE SECURITY GROUP ASSOCIATIONS

- name: Override Security Group Association without no config
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    deploy: switches                                    # choose from ["none", "switches"]
    state: overridden                                   # choose from [merged, replaced, deleted, overridden, query]

- name: Override Security Group Association with config
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    deploy: switches                                    # choose from ["none", "switches"]
    state: overridden                                   # choose from [merged, replaced, deleted, overridden, query]
    config:
      - src_group_name: "LSG_15003"
        dst_group_name: "LSG_15004"
        src_group_id: 15003                             # Group Id associated with src_group_name
        dst_group_id: 15004                             # Group Id associated with dst_group_name
        vrf_name: "MyVRF_50003"
        contract_name: CONTRACT1
        switch:
          - 192.168.1.1
          - 192.168.1.2

# QUERY SECURITY GROUP ASSOCIATIONS

- name: Query Security Groups - without filters
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    deploy: none
    state: query

- name: Query Security Groups - with destination group name
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    deploy: none
    state: query
    config:
      - dst_group_name: "LSG_15002"

- name: Query Security Groups - with vrf name
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    deploy: none
    state: query
    config:
      - vrf_name: "MyVRF_50003"

- name: Query Security Groups - with group id
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    deploy: none
    state: query
    config:
      - src_group_id: 15001

- name: Query Security Groups - with contract name
  cisco.dcnm.dcnm_sgrp_association:
    fabric: Test-Fabric
    deploy: none
    state: query
    config:
      - contract_name: CONTRACT1
"""

#
# WARNING:
#   This file is automatically generated. Take a backup of your changes to this file before
#   manually running cg_run.py script to generate it again
#

import copy
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import (
    Log,
)
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

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_sgrp_association_utils import (
    Paths,
    dcnm_sgrp_association_utils_get_sgrp_association_info,
    dcnm_sgrp_association_utils_get_sgrp_association_payload,
    dcnm_sgrp_association_utils_update_sgrp_association_information,
    dcnm_sgrp_association_utils_get_matching_have,
    dcnm_sgrp_association_utils_get_matching_cfg,
    dcnm_sgrp_association_utils_compare_want_and_have,
    dcnm_sgrp_association_utils_get_sgrp_association_deploy_payload,
    dcnm_sgrp_association_utils_process_delete_payloads,
    dcnm_sgrp_association_utils_process_create_payloads,
    dcnm_sgrp_association_utils_process_modify_payloads,
    dcnm_sgrp_association_utils_process_deploy_payloads,
    dcnm_sgrp_association_utils_get_delete_payload,
    dcnm_sgrp_association_utils_translate_sgrp_association_info,
    dcnm_sgrp_association_utils_get_sync_status,
    dcnm_sgrp_association_utils_get_delete_list,
    dcnm_sgrp_association_utils_get_all_filtered_sgrp_association_objects,
    dcnm_sgrp_association_utils_update_deploy_info,
    dcnm_sgrp_association_utils_check_if_meta,
    dcnm_sgrp_association_utils_validate_devices,
)


# Resource Class object which includes all the required methods and data to configure and maintain Security group associations
class DcnmSgrpAssociation:
    def __init__(self, module):

        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.deploy = module.params["deploy"]
        self.config = copy.deepcopy(module.params.get("config", []))
        self.sgrp_info = {}
        self.sync_info = {}
        self.sgrp_association_info = []
        self.sgrp_association_list = []
        self.want = []
        self.have = []
        self.diff_create = []
        self.diff_modify = []
        self.diff_delete = []
        self.diff_delete_deploy = {}
        self.diff_deploy = {}
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

    def dcnm_sgrp_association_get_diff_query(self):

        """
        Routine to retrieve Security group associations from controller. This routine extracts information provided by the
        user and filters the output based on that.

        Parameters:
            None

        Returns:
            None
        """

        sgrp_association_list = dcnm_sgrp_association_utils_get_all_filtered_sgrp_association_objects(
            self
        )
        if sgrp_association_list != []:
            self.result["response"].extend(sgrp_association_list)

    def dcnm_sgrp_association_get_diff_overridden(self, cfg):

        """
        Routine to override existing Security group associations information with what is included in the playbook. This routine
        deletes all Security group associations objects which are not part of the current config and creates new ones based on what is
        included in the playbook

        Parameters:
            cfg (dct): Configuration information from playbook

        Returns:
            None
        """

        del_list = dcnm_sgrp_association_utils_get_delete_list(self)

        # 'del_list' contains all Security group associations information in 'have' format. Use that to update delete and delete
        # deploy payloads

        for elem in del_list:
            self.dcnm_sgrp_association_update_delete_payloads(elem)

        if cfg == []:
            return

        if self.want:
            # New configuration is included. Delete all existing Security group associations objects and create new objects as requested
            # through the configuration
            self.dcnm_sgrp_association_get_diff_merge()

    def dcnm_sgrp_association_get_diff_deleted(self):

        """
        Routine to get a list of payload information that will be used to delete Security Group Associations.
        This routine updates self.diff_delete with payloads that are used to delete Security Group Associations
        from the server.

        Parameters:
            None

        Returns:
            None
        """

        if self.sgrp_association_info == []:
            # User has not included any config. Delete all existing Security group associations objects from DCNM
            self.dcnm_sgrp_association_get_diff_overridden([])
            return

        for elem in self.sgrp_association_info:

            # Perform any translations that may be required on the sgrp_association_info.
            xelem = dcnm_sgrp_association_utils_translate_sgrp_association_info(
                self, elem
            )
            have = dcnm_sgrp_association_utils_get_sgrp_association_info(
                self, xelem
            )

            if have != []:
                # The above get routine would have matched all required keys. The only one to be matched here
                # is the contract_name to filter the output as required.
                if elem.get("contract_name", None) is not None:
                    if have["contractName"] == elem["contract_name"]:
                        self.dcnm_sgrp_association_update_delete_payloads(have)
                else:
                    self.dcnm_sgrp_association_update_delete_payloads(have)

    def dcnm_sgrp_association_update_delete_payloads(self, have):

        # Get the delete payload based on 'have'
        del_payload = dcnm_sgrp_association_utils_get_delete_payload(
            self, have
        )

        if del_payload not in self.diff_delete:
            self.changed_dict[0]["deleted"].append(del_payload)
            self.diff_delete.append(del_payload)

            if self.deploy != "none":
                # A delete of security group information must be followed by deploy to clean up VRFs and Networks.
                dcnm_sgrp_association_utils_update_deploy_info(
                    self, have, self.diff_delete_deploy
                )
                self.changed_dict[0]["delete_deploy"] = copy.deepcopy(
                    self.diff_delete_deploy
                )

    def dcnm_sgrp_association_get_diff_merge(self):

        """
        Routine to populate a list of payload information in self.diff_create to create/update Security Group Associations.

        Parameters:
            None

        Returns:
            None
        """

        for elem in self.want:

            rc, reasons, have = dcnm_sgrp_association_utils_compare_want_and_have(
                self, elem
            )

            self.log.info(
                f"Compare Want and Have: Return Code = {0}, Reasons = {1}, Have = {2}\n".format(rc, reasons, have)
            )

            if rc == "DCNM_SGRP_ASSOCIATION_CREATE":
                # Object does not exists, create a new one.
                if elem not in self.diff_create:
                    self.changed_dict[0]["merged"].append(elem)
                    self.diff_create.append(elem)
            if rc == "DCNM_SGRP_ASSOCIATION_MERGE":
                # Object already exists, and needs an update
                if elem not in self.diff_modify:
                    self.changed_dict[0]["modified"].append(elem)
                    self.changed_dict[0]["debugs"].append({"REASONS": reasons})
                    self.diff_modify.append(elem)
                    # Modifying existing Security group association requires UUID. Copy that
                    # from 'have'.
                    elem["uuid"] = have["uuid"]

            # Check if "deploy" flag is True. If True, deploy the changes.
            if self.deploy != "none":
                # Before building deploy payload, check
                #  - if something is being created
                #  - if something that is existing is being updated
                #  - if switches are in "In-Sync" state already

                if self.sync_info == {}:
                    self.sync_info = dcnm_sgrp_association_utils_get_sync_status(
                        self
                    )

                dcnm_sgrp_association_utils_get_sgrp_association_deploy_payload(
                    self, elem, rc
                )
            elem.pop("switch")

        if self.diff_deploy != {}:
            self.changed_dict[0]["deploy"].append(
                copy.deepcopy(self.diff_deploy)
            )

    def dcnm_sgrp_association_update_want(self):

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

        match_have = []
        match_cfg = []
        for want in self.want:

            match_have = dcnm_sgrp_association_utils_get_matching_have(
                self, want
            )

            # If have is [], then there is nothing to update
            if match_have != []:
                match_cfg = dcnm_sgrp_association_utils_get_matching_cfg(
                    self, want
                )
                if match_cfg == []:
                    continue

            for melem in match_have:
                dcnm_sgrp_association_utils_update_sgrp_association_information(
                    self, want, melem, match_cfg[0]
                )

    def dcnm_sgrp_association_get_want(self):

        """
        This routine updates self.want with the payload information based on the playbook configuration.

        Parameters:
            None

        Returns:
            None
        """

        if self.config == []:
            return

        for elem in self.sgrp_association_info:

            # If a separate payload is required for every switch included in the payload, then modify this
            # code to loop over the switches. Also the get payload routine should be modified appropriately.

            payload = self.dcnm_sgrp_association_get_payload(elem)
            if payload and payload not in self.want:
                self.want.append(payload)

    def dcnm_sgrp_association_get_have(self):

        """
        Routine to get exisitng sgrp_association information from DCNM that matches information in self.want.
        This routine updates self.have with all the sgrp_association that match the given playbook configuration

        Parameters:
            None

        Returns:
            None
        """

        if self.want == []:
            return

        for elem in self.want:
            have = dcnm_sgrp_association_utils_get_sgrp_association_info(
                self, elem
            )
            if (have != []) and (have not in self.have):
                self.have.append(have)

    def dcnm_sgrp_association_validate_deleted_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        deleted state input. This routine updates self.sgrp_association_info with
        validated playbook information related to deleted state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {
            "src_group_id": {
                "type": "int",
                "range_min": 16,
                "range_max": 65535,
            },
            "dst_group_id": {
                "type": "int",
                "range_min": 16,
                "range_max": 65535,
            },
            "src_group_name": {"type": "str"},
            "dst_group_name": {"type": "str"},
            "contract_name": {"type": "str"},
            "vrf_name": {"type": "str"},
        }

        sgrp_association_info, invalid_params = validate_list_of_dicts(
            cfg, arg_spec
        )
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if sgrp_association_info:
            self.sgrp_association_info.extend(sgrp_association_info)

    def dcnm_sgrp_association_validate_query_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        query state input. This routine updates self.sgrp_association_info with
        validated playbook information related to query state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {
            "src_group_id": {
                "type": "int",
                "range_min": 16,
                "range_max": 65535,
            },
            "dst_group_id": {
                "type": "int",
                "range_min": 16,
                "range_max": 65535,
            },
            "src_group_name": {"type": "str"},
            "dst_group_name": {"type": "str"},
            "contract_name": {"type": "str"},
            "vrf_name": {"type": "str"},
        }

        sgrp_association_info, invalid_params = validate_list_of_dicts(
            cfg, arg_spec
        )
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if sgrp_association_info:
            self.sgrp_association_info.extend(sgrp_association_info)

    def dcnm_sgrp_association_validate_input(self, cfg):

        # The generator hanldes only the case where:
        #   - there are some common paremeters that are included in the playbook
        #   - and a profile which is a 'dict' and which is either based on a template or some fixed structure
        # NOTE: This code assumes that the nested structure will be under a key called 'profile'. If not modify the
        #       same appropriately.
        # This routine generates code to validate the common part and the 'profile' part which is one level nested.
        # Users must modify this code appropriately to hanlde any further nested structures that may be part
        # of playbook input.

        common_spec = {
            "src_group_id": {
                "type": "int",
                "range_min": 16,
                "range_max": 65535,
            },
            "dst_group_id": {
                "type": "int",
                "range_min": 16,
                "range_max": 65535,
            },
            "src_group_name": {"required": True, "type": "str"},
            "dst_group_name": {"required": True, "type": "str"},
            "vrf_name": {"required": True, "type": "str"},
            "contract_name": {"required": True, "type": "str"},
            "switch": {"required": True, "type": "list", "elements": "str"},
        }

        sgrp_association_info, invalid_params = validate_list_of_dicts(
            cfg, common_spec
        )
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        self.sgrp_association_info.append(sgrp_association_info[0])

    def dcnm_sgrp_association_validate_all_input(self):

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
                self.dcnm_sgrp_association_validate_query_state_input(cfg)
            elif self.module.params["state"] == "deleted":
                # config for deleted state is different. So validate deleted state differently
                self.dcnm_sgrp_association_validate_deleted_state_input(cfg)
            else:
                self.dcnm_sgrp_association_validate_input(cfg)
            cfg.remove(citem)

    def dcnm_sgrp_association_get_payload(self, sgrp_association_info):

        """
        This routine builds the complete object payload based on the information in self.want

        Parameters:
            sgrp_association_info (dict): Object information

        Returns:
            sgrp_association_payload (dict): Object payload information populated with appropriate data from playbook config
        """

        sgrp_association_payload = dcnm_sgrp_association_utils_get_sgrp_association_payload(
            self, sgrp_association_info
        )

        return sgrp_association_payload

    def dcnm_sgrp_association_update_switch_info(self):

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

    def dcnm_sgrp_association_translate_playbook_info(
        self, config, ip_sn, hn_sn
    ):

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
            index = 0
            if cfg.get("switch", None) is None:
                continue
            for sw_elem in cfg["switch"][:]:
                if (
                    dcnm_sgrp_association_utils_check_if_meta(self, sw_elem)
                    is True
                ):
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
                dcnm_sgrp_association_utils_validate_devices(self, cfg)

    def dcnm_sgrp_association_send_message_to_dcnm(self):

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

        delete_flag = dcnm_sgrp_association_utils_process_delete_payloads(self)
        create_flag = dcnm_sgrp_association_utils_process_create_payloads(self)
        modify_flag = dcnm_sgrp_association_utils_process_modify_payloads(self)
        deploy_flag = dcnm_sgrp_association_utils_process_deploy_payloads(
            self, self.diff_deploy
        )

        self.log.debug(
            f"Flags: CR = {0}, DL = {1}, MO = {2}, DP = {3}\n".
            format(create_flag, delete_flag, modify_flag, deploy_flag)
        )

        self.result["changed"] = (
            create_flag or modify_flag or delete_flag or deploy_flag
        )

    def dcnm_sgrp_association_update_module_info(self):

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
        config=dict(type="list", elements="dict", default=[]),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "replaced", "overridden", "query"],
        ),
        deploy=dict(
            type="str", choices=["none", "switches"], default="switches"
        ),
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    dcnm_sgrp_association = DcnmSgrpAssociation(module)

    state = module.params["state"]

    dcnm_sgrp_association.log.debug(
        f"######################### BEGIN STATE = {0} ##########################\n".format(state)
    )

    # Initialize the logger
    try:
        logger = Log()
        logger.commit()
    except ValueError as error:
        module.fail_json(msg=str(error))

    # Initialize the Sender object
    sender = Sender()
    sender.ansible_module = module
    dcnm_sgrp_association.rest_send = RestSend(module.params)
    dcnm_sgrp_association.rest_send.response_handler = ResponseHandler()
    dcnm_sgrp_association.rest_send.sender = sender

    # Fill up the version and fabric related details
    dcnm_sgrp_association.dcnm_sgrp_association_update_module_info()

    if dcnm_sgrp_association.config == []:
        if state == "merged" or state == "replaced":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_sgrp_association.config
                )
            )

    dcnm_sgrp_association.dcnm_sgrp_association_update_switch_info()

    dcnm_sgrp_association.dcnm_sgrp_association_translate_playbook_info(
        dcnm_sgrp_association.config,
        dcnm_sgrp_association.ip_sn,
        dcnm_sgrp_association.hn_sn,
    )

    dcnm_sgrp_association.dcnm_sgrp_association_validate_all_input()

    dcnm_sgrp_association.log.info(
        f"Config Info = {0}\n".format(dcnm_sgrp_association.config)
    )
    dcnm_sgrp_association.log.info(
        f"Validated Security Group Association Info = {0}\n".format(dcnm_sgrp_association.sgrp_association_info)
    )

    if (
        module.params["state"] != "query"
        and module.params["state"] != "deleted"
    ):
        dcnm_sgrp_association.dcnm_sgrp_association_get_want()

        dcnm_sgrp_association.log.info(
            f"Want = {0}\n".format(dcnm_sgrp_association.want)
        )
        dcnm_sgrp_association.dcnm_sgrp_association_get_have()

        dcnm_sgrp_association.log.info(
            f"Have = {0}\n".format(dcnm_sgrp_association.have)
        )

        # self.want would have defaulted all optional objects not included in playbook. But the way
        # these objects are handled is different between 'merged' and 'replaced' states. For 'merged'
        # state, objects not included in the playbook must be left as they are and for state 'replaced'
        # they must be purged or defaulted.

        dcnm_sgrp_association.dcnm_sgrp_association_update_want()
        dcnm_sgrp_association.log.info(
            f"Updated Want = {0}\n".format(dcnm_sgrp_association.want)
        )

        dcnm_sgrp_association.log.info(
            f"Security Groups Info = {0}\n".format(dcnm_sgrp_association.sgrp_info)
        )
    if (module.params["state"] == "merged") or (
        module.params["state"] == "replaced"
    ):
        dcnm_sgrp_association.dcnm_sgrp_association_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_sgrp_association.dcnm_sgrp_association_get_diff_deleted()

    if module.params["state"] == "overridden":
        dcnm_sgrp_association.dcnm_sgrp_association_get_diff_overridden(
            dcnm_sgrp_association.config
        )

    if module.params["state"] == "query":
        dcnm_sgrp_association.dcnm_sgrp_association_get_diff_query()

    dcnm_sgrp_association.log.info(
        f"Create Info = {0}\n".format(dcnm_sgrp_association.diff_create)
    )
    dcnm_sgrp_association.log.info(
        f"Replace Info = {0}\n".format(dcnm_sgrp_association.diff_modify)
    )
    dcnm_sgrp_association.log.info(
        f"Delete Info = {0}\n".format(dcnm_sgrp_association.diff_delete)
    )
    dcnm_sgrp_association.log.info(
        f"Deploy Info = {0}\n".format(dcnm_sgrp_association.diff_deploy)
    )
    dcnm_sgrp_association.log.info(
        f"Delete Deploy Info = {0}\n".format(dcnm_sgrp_association.diff_delete_deploy)
    )

    dcnm_sgrp_association.result["diff"] = dcnm_sgrp_association.changed_dict
    dcnm_sgrp_association.changed_dict[0]["debugs"].append(
        {"Managable": dcnm_sgrp_association.managable}
    )
    dcnm_sgrp_association.changed_dict[0]["debugs"].append(
        {"Monitoring": dcnm_sgrp_association.monitoring}
    )

    dcnm_sgrp_association.changed_dict[0]["debugs"].append(
        {"Meta_Switches": dcnm_sgrp_association.meta_switches}
    )

    if dcnm_sgrp_association.diff_create or dcnm_sgrp_association.diff_delete:
        dcnm_sgrp_association.result["changed"] = True

    if module.check_mode:
        dcnm_sgrp_association.result["changed"] = False
        module.exit_json(**dcnm_sgrp_association.result)

    dcnm_sgrp_association.dcnm_sgrp_association_send_message_to_dcnm()

    dcnm_sgrp_association.log.debug(
        f"######################### END STATE = {0} ##########################\n".format(state)
    )

    module.exit_json(**dcnm_sgrp_association.result)


if __name__ == "__main__":
    main()
