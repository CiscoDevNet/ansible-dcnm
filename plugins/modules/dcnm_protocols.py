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
---
module: dcnm_protocols
short_description: Configure Protocols for security contracts on NDFC fabrics
version_added: 3.5.0
description:
    - "This module configures Protocols for security contracts on NDFC fabrics."
author: Praveen Ramoorthy(@praveenramoorthy)
options:
  fabric:
    description:
      - Name of the target fabric for protocols operations.
    type: str
    required: yes
  state:
    description:
      - The required state of the protocols configuration after module completion.
    type: str
    choices: ['merged', 'deleted', 'replaced', 'overridden', 'query']
    default: merged
  config:
    description:
      - A list of dictionaries representing the protocols configuration.
      - Not required for 'query' and 'deleted' states.
    type: list
    elements: dict
    default: []
    suboptions:
      protocol_name:
        description:
          - Name of the protocol.
        type: str
        required: yes
      description:
        description:
          - Description of the protocol.
        type: str
      match_all:
        description:
          - Match all traffic.
        type: bool
        default: false
      match:
        description:
          - A list of dictionaries representing the match criteria.
        type: list
        elements: dict
        suboptions:
          type:
            description:
              - Type of the protocol.
            type: str
            required: yes
            choices: ['ip', 'ipv4', 'ipv6']
          protocol_options:
            description:
              - Protocol options.
            type: str
            default: ""
          fragments:
            description:
              - Match fragments.
            type: bool
            default: false
          stateful:
            description:
              - Match stateful connections.
            type: bool
            default: false
          source_port_range:
            description:
              - Source port range.
            type: str
            default: ""
          destination_port_range:
            description:
              - Destination port range.
            type: str
            default: ""
          tcp_flags:
            description:
              - TCP flags.
            type: str
            choices: ['est', 'ack', 'fin', 'syn', 'rst', 'psh']
            default: ""
          dscp:
            description:
              - DSCP value.
            type: int
"""

EXAMPLES = """
# This module supports the following states:
#
# Merged:
#   Protocols defined in the playbook will be merged into the target fabric.
#     - If the protocol does not exist it will be added.
#     - If the protocol exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Protocols that are not specified in the playbook will be untouched.
#
# Replaced:
#   Protocols defined in the playbook will be replaced in the target fabric.
#     - If the protocol does not exist it will be added.
#     - If the protocol exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - Protocols that are not specified in the playbook will be untouched.
#
# Overridden:
#   Protocols defined in the playbook will be overridden in the target fabric.
#     - If the protocol does not exist it will be added.
#     - If the protocol exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - Protocols that are not specified in the playbook will be deleted.
#
# Deleted:
#   Protocols defined in the playbook will be deleted.
#   If no protocol are provided in the playbook, all protocols present on that DCNM fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the protocols listed in the playbook.
#   If no protocols are provided in the playbook, all protocols present on that DCNM fabric will be returned.

# Merged state - Add a new protocol
# The following example adds a new protocol to the fabric.
# If the protocol already exists, the module will update the protocol with the new configuration.

- name: Add a new protocol
  cisco.dcnm.dcnm_protocols:
    fabric: vxlan-fabric
    state: merged
    config:
      - protocol_name: protocol1
        description: "Protocol 1"
        match_all: false
        match:
          - type: ip
            protocol_options: tcp
            fragments: false
            stateful: false
            source_port_range: "20-30"
            destination_port_range: "50"
            tcp_flags: ""
            dscp: 16

# Replaced state - Replace an existing protocol
# The following example replaces an existing protocol protocol1 in the fabric.
# If the protocol does not exist, the module will create the protocol.

- name: Replace an existing protocol
  cisco.dcnm.dcnm_protocols:
    fabric: vxlan-fabric
    state: replaced
    config:
      - protocol_name: protocol1
        description: "Protocol 1"
        match_all: false
        match:
          - type: ip
            protocol_options: tcp
            fragments: false
            stateful: false
            source_port_range: "10-40"

# Overridden state - Override an existing protocol
# The following example overrides all existing protocol configuration in the fabric.
# If the protocol does not exist, the module will create the protocol.
# If the protocol exists, update the protocol with the new configuration.
# If the protocol exists but is not specified in the playbook, the module will delete the protocol.

- name: Override all existing protocols
  cisco.dcnm.dcnm_protocols:
    fabric: vxlan-fabric
    state: overridden
    config:
      - protocol_name: protocol1
        description: "Protocol 1"
        match_all: false
        match:
          - type: ip
            protocol_options: udp
            source_port_range: "10-40"

# Deleted state - Delete a protocol
# The following example deletes a protocol from the fabric.

- name: Delete a protocol
  cisco.dcnm.dcnm_protocols:
    fabric: vxlan-fabric
    state: deleted
    config:
      - protocol_name

# If no protocol are provided in the playbook, all protocols present on that DCNM fabric will be deleted.

- name: Delete all protocols
  cisco.dcnm.dcnm_protocols:
    fabric: vxlan-fabric
    state: deleted

# Query state - Query a protocol
# The following example queries a protocol from the fabric.

- name: Query a protocol
  cisco.dcnm.dcnm_protocols:
    fabric: vxlan-fabric
    state: query
    config:
      - protocol_name: protocol

# If no protocol are provided in the playbook, all protocols present on that DCNM fabric will be returned.

- name: Query all protocols
  cisco.dcnm.dcnm_protocols:
    fabric: vxlan-fabric
    state: query
"""

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    validate_list_of_dicts,
    dcnm_version_supported,
    get_fabric_inventory_details,
    get_fabric_details,
)

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm_protocols_utils import (
    dcnm_protocols_utils_get_paths,
    dcnm_protocols_utils_get_protocols_info,
    dcnm_protocols_utils_get_protocols_payload,
    dcnm_protocols_utils_compare_want_and_have,
    dcnm_protocols_utils_process_delete_payloads,
    dcnm_protocols_utils_process_create_payloads,
    dcnm_protocols_utils_process_modify_payloads,
    dcnm_protocols_utils_get_delete_payload,
    dcnm_protocols_utils_get_delete_list,
    dcnm_protocols_utils_get_all_filtered_protocols_objects,
)

#
# WARNING:
#   This file is automatically generated. Take a backup of your changes to this file before
#   manually running cg_run.py script to generate it again
#

# Resource Class object which includes all the required methods and data to configure and maintain Protocols


class DcnmProtocols:
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config", []))
        self.protocols_info = []
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
            self.fd = open("dcnm_protocols.log", "a+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.write("\n")
            self.fd.flush()

    def dcnm_protocols_merge_want_and_have(self, want, have):

        """
        Routine to check for mergeable keys in want and merge the same with whatever is already exsiting
        in have.

        Parameters:
            want (dict): Object to be updated with information from have
            have (dict): Existing PROTOCOLS information

        Returns:
            None
        """

        defaulted_keys = []

        # There may be certain objects like "Freeform config" in the parameters which
        # inlcude a list of commands or parameters like member ports which inlcudes a
        # list of interfaces. During MERGE, the values from WANT should be merged
        # to values in have. Identify the actual keys in WANT and HAVE and update the
        # below block of CODE to achieve the merge

        if want.get("description", None):
            have["description"] = want["description"]

        if want.get("matchItems", None):
            if have.get("matchItems", None):
                for match in have["matchItems"]:
                    if match not in want["matchItems"]:
                        want["matchItems"].append(match)

    def dcnm_protocols_get_diff_query(self):

        """
        Routine to retrieve PROTOCOLS from controller. This routine extracts information provided by the
        user and filters the output based on that.

        Parameters:
            None

        Returns:
            None
        """

        protocols_list = dcnm_protocols_utils_get_all_filtered_protocols_objects(self)
        if protocols_list != []:
            self.result["response"].extend(protocols_list)

    def dcnm_protocols_get_diff_overridden(self, cfg):

        """
        Routine to override existing PROTOCOLS information with what is included in the playbook. This routine
        deletes all PROTOCOLS objects which are not part of the current config and creates new ones based on what is
        included in the playbook

        Parameters:
            cfg (dct): Configuration information from playbook

        Returns:
            None
        """

        del_list = dcnm_protocols_utils_get_delete_list(self)

        # 'del_list' contains all PROTOCOLS information in 'have' format. Use that to update delete and delte

        for elem in del_list:
            self.dcnm_protocols_update_delete_payloads(elem)

        if cfg == []:
            return

        if self.want:
            # New configuration is included. Delete all existing PROTOCOLS objects and create new objects as requested
            # through the configuration
            self.dcnm_protocols_get_diff_merge()

    def dcnm_protocols_get_diff_deleted(self):

        """
        Routine to get a list of payload information that will be used to delete Protocols.
        This routine updates self.diff_delete with payloads that are used to delete Protocols
        from the server.

        Parameters:
            None

        Returns:
            None
        """

        if self.protocols_info == []:
            # User has not included any config. Delete all existing PROTOCOLS objects from DCNM
            self.dcnm_protocols_get_diff_overridden([])
            return

        for elem in self.protocols_info:

            # Perform any translations that may be required on the protocols_info.
            have = dcnm_protocols_utils_get_protocols_info(self, elem)

            if have != {}:
                self.dcnm_protocols_update_delete_payloads(have)

    def dcnm_protocols_update_delete_payloads(self, have):

        # Get the delete payload based on 'have'
        del_payload = dcnm_protocols_utils_get_delete_payload(self, have)

        if del_payload != {} and del_payload not in self.diff_delete:
            self.changed_dict[0]["deleted"].append(
                del_payload
            )
            self.diff_delete.append(del_payload)

    def dcnm_protocols_get_diff_merge(self):

        """
        Routine to populate a list of payload information in self.diff_create to create/update Protocols.

        Parameters:
            None

        Returns:
            None
        """

        if not self.want:
            return

        for elem in self.want:

            rc, have = dcnm_protocols_utils_compare_want_and_have(self, elem)

            if rc == "NDFC_PROTOCOLS_CREATE":
                # Object does not exists, create a new one.
                if elem not in self.diff_create:
                    self.changed_dict[0]["merged"].append(elem)
                    self.diff_create.append(elem)
            if rc == "NDFC_PROTOCOLS_MERGE":
                # Object already exists, and needs an update
                if elem not in self.diff_modify:
                    self.changed_dict[0]["modified"].append(elem)

                    # Fields like CONF which are a list of commands should be handled differently in this case.
                    # For existing objects, we will have to merge the current list of commands with already existing
                    # ones in have. For replace, no need to merge them. They must be replaced with what is given.
                    if self.module.params["state"] == "merged":
                        self.dcnm_protocols_merge_want_and_have(elem, have)
                    self.diff_modify.append(elem)

    def dcnm_protocols_get_want(self):

        """
        This routine updates self.want with the payload information based on the playbook configuration.

        Parameters:
            None

        Returns:
            None
        """

        if [] is self.config:
            return

        if not self.protocols_info:
            return

        for elem in self.protocols_info:

            # If a separate payload is required for every switch included in the payload, then modify this
            # code to loop over the switches. Also the get payload routine should be modified appropriately.

            payload = self.dcnm_protocols_get_payload(elem)
            if payload not in self.want:
                self.want.append(payload)

    def dcnm_protocols_get_have(self):

        """
        Routine to get exisitng protocols information from DCNM that matches information in self.want.
        This routine updates self.have with all the protocols that match the given playbook configuration

        Parameters:
            None

        Returns:
            None
        """

        if self.want == []:
            return

        have = dcnm_protocols_utils_get_protocols_info(self, None)
        if (have != []):
            self.have = have

    def dcnm_protocols_validate_deleted_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        deleted state input. This routine updates self.protocols_info with
        validated playbook information related to deleted state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {'protocol_name': {'type': 'str'}}

        protocols_info, invalid_params = validate_list_of_dicts(cfg, arg_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if protocols_info:
            self.protocols_info.extend(protocols_info)

    def dcnm_protocols_validate_query_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the
        query state input. This routine updates self.protocols_info with
        validated playbook information related to query state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = {'protocol_name': {'type': 'str'}}

        protocols_info, invalid_params = validate_list_of_dicts(cfg, arg_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if protocols_info:
            self.protocols_info.extend(protocols_info)

    def dcnm_protocols_validate_input(self, cfg):

        # The generator hanldes only the case where:
        #   - there are some common paremeters that are included in the playbook
        #   - and a profile which is a 'dict' and which is either based on a template or some fixed structure
        # NOTE: This code assumes that the nested structure will be under a key called 'profile'. If not modify the
        #       same appropriately.
        # This routine generates code to validate the common part and the 'profile' part which is one level nested.
        # Users must modify this code appropriately to hanlde any further nested structures that may be part
        # of playbook input.

        common_spec = {
            'protocol_name': {'required': True, 'type': 'str'},
            'description': {'type': 'str'},
            'match_all': {'type': 'bool', 'default': False},
            'match': {'type': 'list'}
        }

        protocol_spec = {
            'type': {'required': True, 'type': 'str', 'choices': ['ip', 'ipv4', 'ipv6']},
            'protocol_options': {'type': 'str', 'default': ""},
            'fragments': {'type': 'bool', 'default': False},
            'stateful': {'type': 'bool', 'default': False},
            'source_port_range': {'type': 'str', 'default': ""},
            'destination_port_range': {'type': 'str', 'default': ""},
            'tcp_flags': {'type': 'str', 'choices': ['est', 'ack', 'fin', 'syn', 'rst', 'psh'], 'default': ""},
            'dscp': {'type': 'int', 'range_min': 0, 'range_max': 63, 'default': None}
        }

        protocols_info, invalid_params = validate_list_of_dicts(cfg, common_spec)
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        for protocol in protocols_info:
            if protocol.get("match"):
                match_info, invalid_att = validate_list_of_dicts(protocol["match"], protocol_spec)
                protocol["match"] = match_info
                invalid_params.extend(invalid_att)

                if invalid_params:
                    mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
                    self.module.fail_json(msg=mesg)

                for match in match_info:
                    if match.get("stateful") or match.get("tcp_flags"):
                        if match.get("protocol_options") and match.get("protocol_options").lower() != "tcp":
                            invalid_params.append("stateful/tcp_flags can be set only for TCP protocol")

                    if match.get("fragments") or match.get("source_port_range") or match.get("destination_port_range"):
                        if match.get("protocol_options") and match.get("protocol_options").lower() not in ["tcp", "udp"]:
                            invalid_params.append("fragments/source_port_range/destination_port_range can be set only for TCP/UDP protocols")

                    match["type"] = match["type"].lower()

                    if match.get("protocol_options", None):
                        match["protocol_options"] = match["protocol_options"].lower()
                    else:
                        del match["protocol_options"]

                    if match.get("tcp_flags", None):
                        match["tcp_flags"] = match["tcp_flags"].lower()
                    else:
                        del match["tcp_flags"]

                    if not match.get("dscp", None):
                        del match["dscp"]
                    if not match.get("source_port_range", None):
                        del match["source_port_range"]
                    if not match.get("destination_port_range", None):
                        del match["destination_port_range"]
                    if not match.get("fragments", None):
                        del match["fragments"]
                    if not match.get("stateful", None):
                        del match["stateful"]

            if protocol.get("match_all"):
                if protocol.get("match"):
                    invalid_params.append("match_all and match cannot be used together")
                matchall = [{"type": "default"}]
                protocol["match"] = matchall

        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        self.protocols_info.append(protocols_info[0])

    def dcnm_protocols_validate_all_input(self):

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
                self.dcnm_protocols_validate_query_state_input(cfg)
            elif self.module.params["state"] == "deleted":
                # config for deleted state is different. So validate deleted state differently
                self.dcnm_protocols_validate_deleted_state_input(cfg)
            else:
                self.dcnm_protocols_validate_input(cfg)
            cfg.remove(citem)

    def dcnm_protocols_get_payload(self, protocols_info):

        """
        This routine builds the complete object payload based on the information in self.want

        Parameters:
            protocols_info (dict): Object information

        Returns:
            protocols_payload (dict): Object payload information populated with appropriate data from playbook config
        """

        protocols_payload = dcnm_protocols_utils_get_protocols_payload(self, protocols_info)

        return protocols_payload

    def dcnm_protocols_send_message_to_dcnm(self):

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

        delete_flag = dcnm_protocols_utils_process_delete_payloads(self)
        create_flag = dcnm_protocols_utils_process_create_payloads(self)
        modify_flag = dcnm_protocols_utils_process_modify_payloads(self)

        self.result["changed"] = (
            create_flag or modify_flag or delete_flag
        )

    def dcnm_protocols_update_module_info(self):

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
        self.paths = dcnm_protocols_utils_get_paths(self.dcnm_version)


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

    dcnm_protocols = DcnmProtocols(module)

    # Fill up the version and fabric related details
    dcnm_protocols.dcnm_protocols_update_module_info()

    state = module.params["state"]

    if [] is dcnm_protocols.config:
        if state == "merged" or state == "replaced":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_protocols.config
                )
            )

    dcnm_protocols.dcnm_protocols_validate_all_input()

    if (
        module.params["state"] != "query" and
        module.params["state"] != "deleted"
    ):
        dcnm_protocols.dcnm_protocols_get_want()

        dcnm_protocols.dcnm_protocols_get_have()

        # self.want would have defaulted all optional objects not included in playbook. But the way
        # these objects are handled is different between 'merged' and 'replaced' states. For 'merged'
        # state, objects not included in the playbook must be left as they are and for state 'replaced'
        # they must be purged or defaulted.

    if (module.params["state"] == "merged") or (
        module.params["state"] == "replaced"
    ):
        dcnm_protocols.dcnm_protocols_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_protocols.dcnm_protocols_get_diff_deleted()

    if module.params["state"] == "overridden":
        dcnm_protocols.dcnm_protocols_get_diff_overridden(dcnm_protocols.config)

    if module.params["state"] == "query":
        dcnm_protocols.dcnm_protocols_get_diff_query()

    dcnm_protocols.result["diff"] = dcnm_protocols.changed_dict

    if dcnm_protocols.diff_create or dcnm_protocols.diff_delete:
        dcnm_protocols.result["changed"] = True

    if module.check_mode:
        dcnm_protocols.result["changed"] = False
        module.exit_json(**dcnm_protocols.result)

    dcnm_protocols.dcnm_protocols_send_message_to_dcnm()

    module.exit_json(**dcnm_protocols.result)


if __name__ == "__main__":
    main()
