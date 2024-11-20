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
__author__ = "Praveen Ramoorthy"

DOCUMENTATION = """
module: dcnm_contracts
short_description: Configure Contracts for security groups in NDFC fabrics
version_added: 3.5.0
description:
    - "This module configures Contracts for security groups in NDFC fabrics"
author: Praveen Ramoorthy(@praveenramoorthy)
options:
  fabric:
    description:
      - Name of the target fabric for contract operations
    type: str
    required: true
  state:
    description:
      - The required state of the contract configuration after module completion
    type: str
    required: false
    choices: ['merged', 'deleted', 'replaced', 'overridden', 'query']
    default: 'merged'
  config:
    description:
      - List of dictionaries representing the contract configuration
      - Not required for 'query' and 'deleted' states
    type: list
    elements: dict
    default: []
    suboptions:
      contract_name:
        description:
          - Name of the contract
        type: str
        required: true
      description:
        description:
          - Description of the contract
        type: str
        required: false
      rules:
        description:
          - List of dictionaries representing the rules of the contract
        type: list
        required: true
        elements: dict
        suboptions:
          direction:
            description:
              - Direction of traffic flow
            type: str
            required: true
            choices: ['bidirectional', 'unidirectional']
          action:
            description:
              - Action to be taken on the traffic
            type: str
            required: true
            choices: ['permit', 'permit_log', 'deny', 'deby_log']
          protocol_name:
            description:
              - Name of the protocol
            type: str
            required: true
"""

EXAMPLES = """
# This module supports the following states:
#
# Merged:
#   Contracts defined in the playbook will be merged into the target fabric.
#     - If the contract does not exist it will be added.
#     - If the contract exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Contracts that are not specified in the playbook will be untouched.
#
# Replaced:
#   Contracts defined in the playbook will be replaced in the target fabric.
#     - If the contract does not exist it will be added.
#     - If the contract exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - Contracts that are not specified in the playbook will be untouched.
#
# Overridden:
#   Contracts defined in the playbook will be overridden in the target fabric.
#     - If the contract does not exist it will be added.
#     - If the contract exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - Contracts that are not specified in the playbook will be deleted.
#
# Deleted:
#   Contracts defined in the playbook will be deleted.
#   If no contracts are provided in the playbook, all contracts present on that DCNM fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the contracts listed in the playbook.
#   If no contracts are provided in the playbook, all contracts present on that DCNM fabric will be returned.


# Merged state - Add or update contracts.
# The below example adds a contract named 'contract1' with a description and rules.

- name: Add a contract
  cisco.dcnm.dcnm_contracts:
    fabric: 'fab1'
    state: 'merged'
    config:
      - contract_name: 'contract1'
        description: 'Contract 1'
        rules:
          - direction: 'bidirectional'
            action: 'permit'
            protocol_name: 'tcp'
          - direction: 'unidirectional'
            action: 'deny'
            protocol_name: 'udp'

# Replaced state - Replace contracts.
# The below example replaces the existing contract named 'contract1' with a new description and rules.
# If the contract does not exist, it will be created.

- name: Replace a contract
  cisco.dcnm.dcnm_contracts:
    fabric: 'fab1'
    state: 'replaced'
    config:
      - contract_name: 'contract1'
        description: 'Contract 1 updated'
        rules:
          - direction: 'bidirectional'
            action: 'permit_log'
            protocol_name: 'https'
          - direction: 'unidirectional'
            action: 'deny_log'
            protocol_name: 'http'

# Overridden state - Override contracts.
# The below example overrides all contracts in the fabric with the contracts defined in the playbook.
# If a contract in playbook does not exist, it will be created. If a contract exists, it will be updated.
# If a contract exists in the fabric but not in the playbook, it will be deleted.

- name: Override contracts
  cisco.dcnm.dcnm_contracts:
    fabric: 'fab1'
    state: 'overridden'
    config:
      - contract_name: 'contract1'
        description: 'Contract 1 updated'
        rules:
          - direction: 'bidirectional'
            action: 'permit_log'
            protocol_name: 'https'
          - direction: 'unidirectional'
            action: 'deny_log'
            protocol_name: 'http'
      - contract_name: 'contract2'
        description: 'Contract 2'
        rules:
          - direction: 'bidirectional'
            action: 'permit'
            protocol_name: 'tcp'

# Deleted state - Delete contracts.
# The below example deletes the contracts named 'contract1' and 'contract2'.

- name: Delete contracts
  cisco.dcnm.dcnm_contracts:
    fabric: 'fab1'
    state: 'deleted'
    config:
      - contract_name: 'contract1'
      - contract_name: 'contract2'

# If no contracts are provided in the playbook, all contracts present on that DCNM fabric will be deleted.

- name: Delete all contracts
  cisco.dcnm.dcnm_contracts:
    fabric: 'fab1'
    state: 'deleted'

# Query state - Query contracts.
# The below example queries the contracts named 'contract1' and 'contract2'.

- name: Query contracts
  cisco.dcnm.dcnm_contracts:
    fabric: 'fab1'
    state: 'query'
    config:
      - contract_name: 'contract1'
      - contract_name: 'contract2'

# If no contracts are provided in the playbook, all contracts present on that DCNM fabric will be returned.

- name: Query all contracts
  cisco.dcnm.dcnm_contracts:
    fabric: 'fab1'
    state: 'query'
"""
import copy
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    validate_list_of_dicts,
    dcnm_version_supported,
    get_fabric_inventory_details,
    get_fabric_details,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_contracts_utils import (
    dcnm_contracts_utils_get_paths,
    dcnm_contracts_utils_get_contracts_info,
    dcnm_contracts_utils_get_contracts_payload,
    dcnm_contracts_utils_compare_want_and_have,
    dcnm_contracts_utils_process_delete_payloads,
    dcnm_contracts_utils_process_create_payloads,
    dcnm_contracts_utils_process_modify_payloads,
    dcnm_contracts_utils_get_delete_payload,
    dcnm_contracts_utils_get_delete_list,
    dcnm_contracts_utils_get_all_filtered_contracts_objects,
)


#
# WARNING:
#   This file is automatically generated. Take a backup of your changes to this file before
#   manually running cg_run.py script to generate it again
#


# Resource Class object which includes all the required methods and data to configure and maintain Contracts
class DcnmContracts:

    def __init__(self, module):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config", []))
        self.contracts_info = []
        self.want = []
        self.have = []
        self.diff_create = []
        self.diff_modify = []
        self.diff_delete = []
        self.arg_specs = {}
        self.fd = None
        self.changed_dict = [
            {
                "merged": [],
                "deleted": [],
                "modified": [],
                "query": [],
                "debugs": [],
            }
        ]

        self.result = dict(changed=False, diff=[], response=[])

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("dcnm_contracts.log", "a+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.write("\n")
            self.fd.flush()

    def dcnm_contracts_merge_want_and_have(self, want, have):

        """
        Routine to check for mergeable keys in want and merge the same with whatever is already exsiting
        in have.

        Parameters:
            want (dict): Object to be updated with information from have
            have (dict): Existing CONTRACTS information

        Returns:
            None
        """

        # Code is generated for comparing "nvPairs" objects alone. If there are other nested structures
        # in the want and have objects that need to be compared, add the necessary code here.

        # There may be certain objects like "Freeform config" in the parameters which
        # inlcude a list of commands or parameters like member ports which inlcudes a
        # list of interfaces. During MERGE, the values from WANT should be merged
        # to values in have. Identify the actual keys in WANT and HAVE and update the
        # below block of CODE to achieve the merge

        if want.get("description", None):
            have["description"] = want["description"]

        if want.get("rules", None):
            if have.get("rules", None):
                for rule in have["rules"]:
                    if rule not in want["rules"]:
                        want["rules"].append(rule)

    def dcnm_contracts_get_diff_query(self):

        """
        Routine to retrieve CONTRACTS from controller. This routine extracts information provided by the
        user and filters the output based on that.

        Parameters:
            None

        Returns:
            None
        """

        contracts_list = dcnm_contracts_utils_get_all_filtered_contracts_objects(self)
        if contracts_list != []:
            self.result["response"].extend(contracts_list)

    def dcnm_contracts_get_diff_overridden(self, cfg):

        """
        Routine to override existing CONTRACTS information with what is included in the playbook. This routine
        deletes all CONTRACTS objects which are not part of the current config and creates new ones based on what is
        included in the playbook

        Parameters:
            cfg (dct): Configuration information from playbook

        Returns:
            None
        """

        del_list = dcnm_contracts_utils_get_delete_list(self)

        # 'del_list' contains all CONTRACTS information in 'have' format. Use that to update delete payloads

        for elem in del_list:
            self.dcnm_contracts_update_delete_payloads(elem)

        if cfg == []:
            return

        if self.want:
            # New configuration is included. Delete all existing CONTRACTS objects and create new objects as requested
            # through the configuration
            self.dcnm_contracts_get_diff_merge()

    def dcnm_contracts_get_diff_deleted(self):

        """
        Routine to get a list of payload information that will be used to delete Contracts.
        This routine updates self.diff_delete with payloads that are used to delete Contracts
        from the server.

        Parameters:
            None

        Returns:
            None
        """

        if self.contracts_info == []:
            # User has not included any config. Delete all existing CONTRACTS objects from DCNM
            self.dcnm_contracts_get_diff_overridden([])
            return

        for elem in self.contracts_info:

            # Perform any translations that may be required on the contracts_info.
            have = dcnm_contracts_utils_get_contracts_info(self, elem)

            if have != {}:
                self.dcnm_contracts_update_delete_payloads(have)

    def dcnm_contracts_update_delete_payloads(self, have):

        # Get the delete payload based on 'have'
        del_payload = dcnm_contracts_utils_get_delete_payload(self, have)

        if del_payload != {} and del_payload not in self.diff_delete:
            self.changed_dict[0]["deleted"].append(
                del_payload
            )
            self.diff_delete.append(del_payload)

    def dcnm_contracts_get_diff_merge(self):

        """
        Routine to populate a list of payload information in self.diff_create to create/update Contracts.

        Parameters:
            None

        Returns:
            None
        """

        if not self.want:
            return

        for elem in self.want:

            rc, have = dcnm_contracts_utils_compare_want_and_have(self, elem)
            msg = f"Compare Want and Have: Return Code = {rc},  Have = {have}\n"
            self.log.info(msg)
            if rc == "NDFC_CONTRACTS_CREATE":
                # Object does not exists, create a new one.
                if elem not in self.diff_create:
                    self.changed_dict[0]["merged"].append(elem)
                    self.diff_create.append(elem)
            if rc == "NDFC_CONTRACTS_MERGE":
                # Object already exists, and needs an update
                if elem not in self.diff_modify:
                    self.changed_dict[0]["modified"].append(elem)

                    # Fields like CONF which are a list of commands should be handled differently in this case.
                    # For existing objects, we will have to merge the current list of commands with already existing
                    # ones in have. For replace, no need to merge them. They must be replaced with what is given.
                    if self.module.params["state"] == "merged":
                        self.dcnm_contracts_merge_want_and_have(elem, have)
                    self.diff_modify.append(elem)

    def dcnm_contracts_get_want(self):

        """
        This routine updates self.want with the payload information based on the playbook configuration.

        Parameters:
            None

        Returns:
            None
        """

        if [] is self.config:
            return

        if not self.contracts_info:
            return

        for elem in self.contracts_info:

            # If a separate payload is required for every switch included in the payload, then modify this
            # code to loop over the switches. Also the get payload routine should be modified appropriately.

            payload = self.dcnm_contracts_get_payload(elem)
            if payload not in self.want:
                self.want.append(payload)

    def dcnm_contracts_get_have(self):

        """
        Routine to get exisitng contracts information from DCNM that matches information in self.want.
        This routine updates self.have with all the contracts that match the given playbook configuration

        Parameters:
            None

        Returns:
            None
        """

        if self.want == []:
            return

        have = dcnm_contracts_utils_get_contracts_info(self, None)
        if (have != []):
            self.have = have

    def dcnm_contracts_validate_deleted_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        deleted state input. This routine updates self.contracts_info with
        validated playbook information related to deleted state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {'contract_name': {'type': 'str'}}

        contracts_info, invalid_params = validate_list_of_dicts(cfg, arg_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if contracts_info:
            self.contracts_info.extend(contracts_info)

    def dcnm_contracts_validate_query_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        query state input. This routine updates self.contracts_info with
        validated playbook information related to query state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {'contract_name': {'type': 'str'}}

        contracts_info, invalid_params = validate_list_of_dicts(cfg, arg_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if contracts_info:
            self.contracts_info.extend(contracts_info)

    def dcnm_contracts_validate_input(self, cfg):

        # The generator hanldes only the case where:
        #   - there are some common paremeters that are included in the playbook
        #   - and a profile which is a 'dict' and which is either based on a template or some fixed structure
        # NOTE: This code assumes that the nested structure will be under a key called 'profile'. If not modify the
        #       same appropriately.
        # This routine generates code to validate the common part and the 'profile' part which is one level nested.
        # Users must modify this code appropriately to hanlde any further nested structures that may be part
        # of playbook input.

        common_spec = {
            'contract_name': {'required': True, 'type': 'str'},
            'description': {'type': 'str'},
            'rules': {'required': True, 'type': 'list', 'elements': 'dict'}
        }
        rules_spec = {
            'direction': {'required': True, 'type': 'str', 'choices': ['bidirectional', 'unidirectional']},
            'action': {'required': True, 'type': 'str', 'choices': ['permit', 'permit_log', 'deny', 'deby_log']},
            'protocol_name': {'required': True, 'type': 'str'}
        }

        # Even 'common_spec' may require some updates based on other information.
        # dcnm_contracts_utils_update_common_spec(self, common_spec)

        contracts_info, invalid_params = validate_list_of_dicts(cfg, common_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        for contract in contracts_info:
            if contract.get("rules"):
                rules_info, invalid_att = validate_list_of_dicts(contract['rules'], rules_spec)
                contract["rules"] = rules_info
                invalid_params.extend(invalid_att)

            self.contracts_info.append(contract)

        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

    def dcnm_contracts_validate_all_input(self):

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
                self.dcnm_contracts_validate_query_state_input(cfg)
            elif self.module.params["state"] == "deleted":
                # config for deleted state is different. So validate deleted state differently
                self.dcnm_contracts_validate_deleted_state_input(cfg)
            else:
                self.dcnm_contracts_validate_input(cfg)
            cfg.remove(citem)

    def dcnm_contracts_get_payload(self, contracts_info):

        """
        This routine builds the complete object payload based on the information in self.want

        Parameters:
            contracts_info (dict): Object information

        Returns:
            contracts_payload (dict): Object payload information populated with appropriate data from playbook config
        """

        contracts_payload = dcnm_contracts_utils_get_contracts_payload(self, contracts_info)

        return contracts_payload

    def dcnm_contracts_send_message_to_dcnm(self):

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

        delete_flag = dcnm_contracts_utils_process_delete_payloads(self)
        create_flag = dcnm_contracts_utils_process_create_payloads(self)
        modify_flag = dcnm_contracts_utils_process_modify_payloads(self)

        msg = f"Flags: CR = {create_flag}, DL = {delete_flag}, MO = {modify_flag}\n"
        self.log.debug(msg)

        self.result["changed"] = (
            create_flag or modify_flag or delete_flag
        )

    def dcnm_contracts_update_module_info(self):

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

        self.fabric_info = get_fabric_details(self.module, self.fabric)
        self.paths = dcnm_contracts_utils_get_paths(self.dcnm_version)


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
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    dcnm_contracts = DcnmContracts(module)

    # Fill up the version and fabric related details
    dcnm_contracts.dcnm_contracts_update_module_info()

    state = module.params["state"]

    # Logging setup
    try:
        log = Log()
        log.commit()
    except ValueError as error:
        module.fail_json(str(error))

    msg = f"######################### BEGIN STATE = {state} ##########################\n"
    dcnm_contracts.log.debug(msg)

    if [] is dcnm_contracts.config:
        if state == "merged" or state == "replaced":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_contracts.config
                )
            )

    dcnm_contracts.dcnm_contracts_validate_all_input()

    msg = f"Config Info = {dcnm_contracts.config}\n"
    dcnm_contracts.log.info(msg)

    msg = f"Validated Security Group Association Info = {dcnm_contracts.contracts_info}\n"
    dcnm_contracts.log.info(msg)

    if (
        module.params["state"] != "query" and
        module.params["state"] != "deleted"
    ):
        dcnm_contracts.dcnm_contracts_get_want()

        msg = f"Want = {dcnm_contracts.want}\n"
        dcnm_contracts.log.info(msg)

        dcnm_contracts.dcnm_contracts_get_have()

        msg = f"Have = {dcnm_contracts.have}\n"
        dcnm_contracts.log.info(msg)

        msg = f"Updated Want = {dcnm_contracts.want}\n"
        dcnm_contracts.log.info(msg)

        # self.want would have defaulted all optional objects not included in playbook. But the way
        # these objects are handled is different between 'merged' and 'replaced' states. For 'merged'
        # state, objects not included in the playbook must be left as they are and for state 'replaced'
        # they must be purged or defaulted.

    if (module.params["state"] == "merged") or (
        module.params["state"] == "replaced"
    ):
        dcnm_contracts.dcnm_contracts_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_contracts.dcnm_contracts_get_diff_deleted()

    if module.params["state"] == "overridden":
        dcnm_contracts.dcnm_contracts_get_diff_overridden(dcnm_contracts.config)

    if module.params["state"] == "query":
        dcnm_contracts.dcnm_contracts_get_diff_query()

    msg = f"Create Info = {dcnm_contracts.diff_create}\n"
    dcnm_contracts.log.info(msg)

    msg = f"Replace Info = {dcnm_contracts.diff_modify}\n"
    dcnm_contracts.log.info(msg)

    msg = f"Delete Info = {dcnm_contracts.diff_delete}\n"
    dcnm_contracts.log.info(msg)

    dcnm_contracts.result["diff"] = dcnm_contracts.changed_dict

    if dcnm_contracts.diff_create or dcnm_contracts.diff_delete or dcnm_contracts.diff_modify:
        dcnm_contracts.result["changed"] = True

    if module.check_mode:
        dcnm_contracts.result["changed"] = False
        module.exit_json(**dcnm_contracts.result)

    dcnm_contracts.dcnm_contracts_send_message_to_dcnm()

    msg = f"######################### END STATE = {state} ##########################\n"
    dcnm_contracts.log.debug(msg)

    module.exit_json(**dcnm_contracts.result)


if __name__ == "__main__":
    main()
