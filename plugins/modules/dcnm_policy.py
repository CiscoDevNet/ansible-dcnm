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
__author__ = "Mallik Mudigonda"

DOCUMENTATION = """
---
module: dcnm_policy
short_description: DCNM Ansible Module for managing policies.
version_added: "1.1.0"
description:
    - DCNM Ansible Module for Creating, Deleting, Querying and Modifying policies
author: Mallik Mudigonda(@mmudigon)
options:
  fabric:
    description:
    - Name of the target fabric for policy operations
    type: str
    required: true

  state:
    description:
    - The required state of the configuration after module completion.
    type: str
    required: false
    choices:
      - merged
      - deleted
      - query
    default: merged

  deploy:
    description:
    - A flag specifying if a policy is to be deployed on the switches
    type: bool
    required: false
    default: true

  config:
    description:
    - A list of dictionaries containing policy and switch information
    type: list
    elements: dict
    suboptions:
      name:
        description:
        - This can be one of the following
          a) Template Name - A unique name identifying the template. Please note that a template name can be used by
             multiple policies and hence a template name does not identify a policy uniquely.
          b) Policy ID     - A unique ID identifying a policy. Policy ID MUST be used for modifying policies since
             template names cannot uniquely identify a policy
        type: str
        required: true

      description:
        description:
        - Description of the policy. The description may include the details regarding the policy i.e. the arguments if
          any etc.
        type: str
        required: false
        default: ''

      priority:
        description:
        - Priority associated with the policy
        type: str
        required: false
        default: '500'

      create_additional_policy:
        description:
        - A flag indicating if a policy is to be created even if an identical policy already exists
        type: bool
        required: false
        default: true

      policy_vars:
        description:
        - A set of arguments required for creating and deploying policies. The arguments are specific to each policy and depends
          on the tmeplate that is used by the policy.
        type: dict
        required: false
        default: {}

      switch:
        description:
        - A dictionary of switches and associated policy information. All switches in this list will be deployed with only those policies
          that are included under "policies" object i.e. 'policies' object will override the list of policies for this particular switch.
          If 'policies' object is not included, then other policies specified in the configurstion will be deployed to these switches.
        type: list
        elements: dict
        suboptions:
          ip:
            description:
            - IP address of the switch where the policy is to be deployed. This can be IPV4 address, IPV6 address or hostname
            type: str
            required: true

          policies:
            description:
            - A list of policies to be deployed on the switch. Note only policies included here will be deployed on the switch irrespective of
              other polcies included in the configuration.
            type: list
            elements: dict
            required: false
            default: []
            suboptions:
              name:
                description:
                - This can be one of the following
                  a) Template Name - A unique name identifying the template. Please note that a template name can be used by
                     multiple policies and hence a template name does not identify a policy uniquely.
                  b) Policy ID     - A unique ID identifying a policy. Policy ID MUST be used for modifying policies since
                     template names cannot uniquely identify a policy
                type: str
                required: true

              description:
                description:
                - Description of the policy. The description may include the details regarding the policy
                type: str
                required: false
                default: ''

              priority:
                description:
                - Priority associated with the policy
                type: str
                required: false
                default: '500'

              create_additional_policy:
                description:
                - A flag indicating if a policy is to be created even if an identical policy already exists
                type: bool
                required: false
                default: true

              policy_vars:
                description:
                - A set of arguments required for creating and deploying policies. The arguments are specific to each policy and that depends
                  on the tmeplate that is used by the policy.
                type: dict
                required: false
                default: {}
"""

EXAMPLES = """

# States:
# This module supports the following states:
#
# Merged:
#   Policies defined in the playbook will be merged into the target fabric.
#
#   The policies listed in the playbook will be created if not already present on the DCNM
#   server. If the policy is already present and the configuration information included
#   in the playbook is either different or not present in DCNM, then the corresponding
#   information is added to the policy on DCNM. If an policy mentioned in playbook
#   is already present on DCNM and there is no difference in configuration, no operation
#   will be performed for such policy.
#
# Deleted:
#   Policies defined in the playbook will be deleted in the target fabric.
#
#   WARNING: Deleting a policy will deploy all pending configurations on the impacted switches.
#
# Query:
#   Returns the current DCNM state for the policies listed in the playbook.

# CREATE POLICY

# NOTE: In the following create task, policies identified by template names template_101,
#       template_102, and template_103 are deployed on ansible_switch2 where as policies
#       template_104 and template_105 are the only policies installed on ansible_switch1.

- name: Create different policies
  cisco.dcnm.dcnm_policy:
    fabric: "{{ ansible_it_fabric }}"
    state: merged
    deploy: true
    config:
      - name: template_101  # This must be a valid template name
        create_additional_policy: false  # Do not create a policy if it already exists
        priority: 101

      - name: template_102  # This must be a valid template name
        create_additional_policy: false  # Do not create a policy if it already exists
        description: 102 - No piority given

      - name: template_103  # This must be a valid template name
        create_additional_policy: false  # Do not create a policy if it already exists
        description: Both description and priority given
        priority: 500

      - switch:
          - ip: "{{ ansible_switch1 }}"
            policies:
              - name: template_104  # This must be a valid template name
                create_additional_policy: false  # Do not create a policy if it already exists

              - name: template_105  # This must be a valid template name
                create_additional_policy: false  # Do not create a policy if it already exists
          - ip: "{{ ansible_switch2 }}"

# CREATE POLICY (including arguments)

# NOTE: The actual arguments to be included depends on the template used to create the policy

- name: Create policy including required variables
  cisco.dcnm.dcnm_policy:
    fabric: "{{ ansible_it_fabric }}"
    config:
      - name: my_base_ospf               # This must be a valid template name
        create_additional_policy: false  # Do not create a policy if it already exists
        priority: 101
        policy_vars:
          OSPF_TAG: 2000
          LOOPBACK_IP: 10.122.84.108

      - switch:
          - ip: "{{ ansible_switch1 }}"

# MODIFY POLICY

# NOTE: Since there can be multiple policies with the same template name, policy-id MUST be used
#       to modify a particular policy.

- name: Modify different policies
  cisco.dcnm.dcnm_policy:
    fabric: "{{ ansible_it_fabric }}"
    state: merged
    deploy: true
    config:
      - name: POLICY-101101  # This must be a valid POLICY ID
        create_additional_policy: false  # Do not create a policy if it already exists
        priority: 101

      - name: POLICY-102102  # This must be a valid POLICY ID
        create_additional_policy: false  # Do not create a policy if it already exists
        description: 102 - No piority given

      - name: POLICY-103103  # This must be a valid POLICY ID
        create_additional_policy: false  # Do not create a policy if it already exists
        description: Both description and priority given
        priority: 500

      - switch:
          - ip: "{{ ansible_switch1 }}"
            policies:
              - name: POLICY-104104  # This must be a valid POLICY ID
                create_additional_policy: false  # Do not create a policy if it already exists

              - name: POLICY-105105  # This must be a valid POLICY ID
                create_additional_policy: false  # Do not create a policy if it already exists
              - ip: "{{ ansible_switch2 }}"

# DELETE POLICY

# NOTE: In the case of deleting policies using template names, all policies using the template name
#       will be deleted. To delete specific policy, policy-ids must be used

- name: Delete policies using template name
  cisco.dcnm.dcnm_policy:
    fabric: "{{ ansible_it_fabric }}"
    state: deleted          # only choose form [merged, deleted, query]
    config:
      - name: template_101  # name is mandatory
      - name: template_102  # name is mandatory
      - name: template_103  # name is mandatory
      - name: template_104  # name is mandatory
      - name: template_105  # name is mandatory
      - switch:
          - ip: "{{ ansible_switch1 }}"
          - ip: "{{ ansible_switch2 }}"

- name: Delete policies using policy-id
  cisco.dcnm.dcnm_policy:
    fabric: "{{ ansible_it_fabric }}"
    state: deleted          # only choose form [merged, deleted, query]
    config:
      - name: POLICY-101101  # name is mandatory
      - name: POLICY-102102  # name is mandatory
      - name: POLICY-103103  # name is mandatory
      - name: POLICY-104104  # name is mandatory
      - name: POLICY-105105  # name is mandatory
      - switch:
          - ip: "{{ ansible_switch1 }}"
          - ip: "{{ ansible_switch2 }}"

# QUERY

# NOTE: In the case of Query using template names, all policies that have a matching template name will be
#       returned

- name: Query all policies from the specified switches
  cisco.dcnm.dcnm_policy:
    fabric: "{{ ansible_it_fabric }}"
    state: query
    config:
      - switch:
          - ip: "{{ ansible_switch1 }}"
          - ip: "{{ ansible_switch2 }}"

- name: Query policies matching template names
  cisco.dcnm.dcnm_policy:
    fabric: "{{ ansible_it_fabric }}"
    state: query
    config:
      - name: template_101
      - name: template_102
      - name: template_103
      - switch:
          - ip: "{{ ansible_switch1 }}"

- name: Query policies using policy-ids
  cisco.dcnm.dcnm_policy:
    fabric: "{{ ansible_it_fabric }}"
    state: query
    config:
      - name: POLICY-101101
      - name: POLICY-102102
      - name: POLICY-103103
      - switch:
          - ip: "{{ ansible_switch1 }}"
"""

import json
import re
import copy
import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    get_fabric_inventory_details,
    dcnm_get_ip_addr_info,
    validate_list_of_dicts,
    get_ip_sn_dict,
    dcnm_version_supported,
)


class DcnmPolicy:

    dcnm_policy_paths = {
        11: {
            "POLICY_WITH_ID": "/rest/control/policies/{}",
            "POLICY_GET_SWITCHES": "/rest/control/policies/switches?serialNumber={}",
            "POLICY_BULK_CREATE": "/rest/control/policies/bulk-create",
            "POLICY_MARK_DELETE": "/rest/control/policies/{}/mark-delete",
            "POLICY_DEPLOY": "/rest/control/policies/deploy",
            "POLICY_CFG_DEPLOY": "/rest/control/fabrics/{}/config-deploy/",
            "POLICY_WITH_POLICY_ID": "/rest/control/policies/{}",
            "CONFIG_PREVIEW": "/rest/control/fabrics/{}/config-preview/",
        },
        12: {
            "POLICY_WITH_ID": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/{}",
            "POLICY_GET_SWITCHES": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/switches?serialNumber={}",
            "POLICY_BULK_CREATE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/bulk-create",
            "POLICY_MARK_DELETE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/{}/mark-delete",
            "POLICY_DEPLOY": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/deploy",
            "POLICY_CFG_DEPLOY": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-deploy/",
            "POLICY_WITH_POLICY_ID": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/{}",
            "CONFIG_PREVIEW": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-preview/",
        },
    }

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.config = copy.deepcopy(module.params.get("config"))
        self.deploy = True  # Global 'deploy' flag
        self.pb_input = []
        self.check_mode = False
        self.policy_info = []
        self.want = []
        self.have = []
        self.have_all_list = []
        self.diff_create = []
        self.diff_modify = []
        self.diff_delete = []
        self.diff_query = []
        self.deploy_payload = []
        self.fd = None
        self.changed_dict = [
            {
                "merged": [],
                "deleted": [],
                "deploy": [],
                "query": [],
                "skipped": [],
            }
        ]

        self.dcnm_version = dcnm_version_supported(self.module)

        self.inventory_data = get_fabric_inventory_details(
            self.module, self.fabric
        )

        # Get all switches which are managable. Will be required to check deploy status.
        self.managable = [
            self.inventory_data[key]["serialNumber"]
            for key in self.inventory_data.keys()
            if self.inventory_data[key]["managable"]
        ]
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)

        self.result = dict(changed=False, diff=[], response=[])
        self.paths = self.dcnm_policy_paths[self.dcnm_version]

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("policy.log", "w+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.write("\n")
            self.fd.flush()

    # Flatten the incoming config database and have the required fileds updated.
    # This modified config DB will be used while creating payloads. To avoid
    # messing up the incoming config make a copy of it.
    def dcnm_policy_copy_config(self):

        if None is self.config:
            return
        for cfg in self.config:
            self.pb_input.append(copy.deepcopy(cfg))

    def dcnm_policy_validate_input(self):

        policy_spec = dict(
            name=dict(required=True, type="str"),
            create_additional_policy=dict(
                required=False, type="bool", default=True
            ),
            description=dict(required=False, type="str", default=""),
            priority=dict(required=False, type=int, default=500),
            policy_vars=dict(required=False, type=dict, default={}),
            switch=dict(required=True, type="list"),
        )

        for cfg in self.config:

            clist = []
            clist.append(cfg)
            policy_info, invalid_params = validate_list_of_dicts(
                clist, policy_spec
            )
            if invalid_params:
                mesg = 'Invalid parameters in playbook: while processing policy "{0}", Error: {1}'.format(
                    cfg["name"], invalid_params
                )
                self.module.fail_json(msg=mesg)
            self.policy_info.extend(policy_info)

    def dcnm_get_policy_payload_with_template_name(self, pelem, sw):

        policy_payload = {
            "source": "",
            "serialNumber": "",
            "entityType": "SWITCH",
            "entityName": "SWITCH",
            "templateName": "",
            "priority": "",
            "nvPairs": {},
        }

        policy_payload["serialNumber"] = self.ip_sn[sw]
        policy_payload["templateName"] = pelem["name"]
        policy_payload["description"] = pelem["description"]
        policy_payload["priority"] = pelem["priority"]
        policy_payload["create_additional_policy"] = pelem[
            "create_additional_policy"
        ]

        policy_payload["policy_id_given"] = False

        if pelem.get("policy_vars", None) is not None:
            # Given policy has arguments. Add these to the payload
            for var in pelem["policy_vars"]:
                policy_payload["nvPairs"][var] = pelem["policy_vars"][var]

        return policy_payload

    def dcnm_get_policy_payload_with_policy_id(self, pelem, sw):

        policy_payload = {
            "id": "",
            "source": "",
            "serialNumber": "",
            "policyId": "",
            "entityType": "SWITCH",
            "entityName": "SWITCH",
            "templateName": "",
            "priority": "",
            "description": "",
            "nvPairs": {},
        }

        # Get the existing policy and get the templateName, id etc.
        policy = self.dcnm_policy_get_policy_info_from_dcnm(pelem["name"])

        if policy == []:
            return policy

        policy_payload["id"] = policy["id"]
        policy_payload["serialNumber"] = self.ip_sn[sw]
        policy_payload["policyId"] = policy["policyId"]
        policy_payload["description"] = pelem["description"]
        policy_payload["templateName"] = policy["templateName"]
        policy_payload["priority"] = pelem["priority"]
        policy_payload["create_additional_policy"] = pelem[
            "create_additional_policy"
        ]
        policy_payload["nvPairs"] = policy["nvPairs"]

        policy_payload["policy_id_given"] = True

        if pelem.get("policy_vars", None) is not None:
            # Given policy has arguments. Add these to the payload
            for var in pelem["policy_vars"]:
                policy_payload["nvPairs"][var] = pelem["policy_vars"][var]

        return policy_payload

    def dcnm_policy_get_want(self):

        if None is self.config:
            return

        if not self.policy_info:
            return

        # self.policy_info is a list of directories each having config related to a particular policy
        for pelem in self.policy_info:
            for sw in pelem["switch"]:
                if "POLICY-" in pelem["name"]:
                    # Policy ID is given. Get the 'PUT' payload which will be used for
                    # updating a policy
                    policy_payload = self.dcnm_get_policy_payload_with_policy_id(
                        pelem, sw
                    )
                else:
                    # Template name is given. Get the 'POST' payload which is used for creating
                    # new policies
                    policy_payload = self.dcnm_get_policy_payload_with_template_name(
                        pelem, sw
                    )
                if policy_payload:
                    self.want.append(policy_payload)

    def dcnm_policy_get_policy_info_from_dcnm(self, policy_id):

        path = self.paths["POLICY_WITH_ID"].format(policy_id)

        resp = dcnm_send(self.module, "GET", path)

        if (
            resp
            and (resp["RETURN_CODE"] == 200)
            and (resp["MESSAGE"] == "OK")
            and resp["DATA"]
        ):
            return resp["DATA"]
        else:
            return []

    def dcnm_policy_get_all_policies(self, snos):

        path = self.paths["POLICY_GET_SWITCHES"].format(snos)

        # Append ',' separated snos ro the path and get all policies. Then filter the list based on the
        # given template name

        resp = dcnm_send(self.module, "GET", path)

        if (
            resp
            and (resp["RETURN_CODE"] == 200)
            and (resp["MESSAGE"] == "OK")
            and resp["DATA"]
        ):
            return resp["DATA"]
        else:
            return []

    def dcnm_policy_get_snos_string(self, want):

        snos = ""
        for pol in want:
            if pol["serialNumber"] not in snos:
                if snos != "":
                    snos = snos + ","
                snos = snos + pol["serialNumber"]
        return snos

    def dcnm_policy_get_have(self):

        if not self.want:
            return

        # For 'deleted' state, we do this in the diff_deleted function
        if self.module.params.get("state") == "deleted":
            return

        # Get all the snos as a string separated by ','
        snos = self.dcnm_policy_get_snos_string(self.want)

        # Policies cannot be obtained by using template names. Policies have 'policy-id' which is the key
        # to get a policy. Since playbook includes only template names, we need to get all policies from
        # all the switches included in playbook, and then filter them out using template names.
        plist = self.dcnm_policy_get_all_policies(snos)

        # Filter the list of policies and keep only those that are matching
        # self.want may have duplicates because we allow the same policy to be created multiple times. So
        # make sure self.have does not have duplicates
        match_pol = [
            pl
            for pl in plist
            for wp in self.want
            if (pl["templateName"] == wp["templateName"])
        ]

        # match_pol can be a list of dicts, containing duplicates. Remove the duplicate entries
        for pol in match_pol:
            if pol not in self.have:
                self.have.append(pol)

    def dcnm_policy_compare_nvpairs(self, pnv, hnv):

        if pnv is None:
            return "DCNM_POLICY_MATCH"

        for k in pnv.keys():
            pv = str(pnv.get(k, None))
            hv = str(hnv.get(k, None))
            if pv != hv:
                return "DCNM_POLICY_DONT_MATCH"
        return "DCNM_POLICY_MATCH"

    def dcnm_policy_compare_policies(self, policy):

        found = False

        if self.have == []:
            return ("DCNM_POLICY_ADD_NEW", None)

        # For modify cases, we need to match the exact policy and so we should compare
        # policyIds. For create cases use templateName key.

        if policy.get("policyId", None) is not None:
            key = "policyId"
        else:
            key = "templateName"

        for have in self.have:
            if (have[key] == policy[key]) and (
                have.get("serialNumber", None) == policy["serialNumber"]
            ):
                found = True
                # Have a policy with matching template name. Check for other objects
                if have.get("description", None) == policy["description"]:
                    if have.get("priority", None) == policy["priority"]:
                        if (
                            self.dcnm_policy_compare_nvpairs(
                                policy.get("nvPairs", None),
                                have.get("nvPairs", None),
                            )
                            == "DCNM_POLICY_MATCH"
                        ):
                            return ("DCNM_POLICY_DONT_ADD", have["policyId"])
        if found is True:
            # Found a matching policy with the given template name, but other objects don't match.
            # Go ahead and merge the objects into the existing policy
            return ("DCNM_POLICY_MERGE", have["policyId"])
        else:
            return ("DCNM_POLICY_ADD_NEW", None)

    def dcnm_policy_get_diff_merge(self):

        self.diff_create = []
        self.diff_delete = []
        self.diff_query = []
        self.valid_fail = []
        policy_id = None

        if not self.want:
            return

        for policy in self.want:

            # For create self.want will contain template names. For modifying policies users must
            # provide the policy id only. Based on what is given, the payloads in self.want will be
            # built. If 'self.want' contains 'policyId', then it means user has provided policyId
            # and so this will be a UPDATE case

            rc, policy_id = self.dcnm_policy_compare_policies(policy)

            if rc == "DCNM_POLICY_ADD_NEW":
                # A policy does not exists, create a new one. Even if one exists, if create_additional_policy
                # is specified, then create the policy
                if (policy not in self.diff_create) or (
                    policy["create_additional_policy"] is True
                ):
                    self.changed_dict[0]["merged"].append(policy)
                    self.diff_create.append(policy)
            elif rc == "DCNM_POLICY_MERGE":
                # A policy exists and it needs to be updated
                # Merge is allowed only in the case of user providing policyId in place of templateName.
                # This is because there can be multiple policies with the same templateName and hence we
                # will not know which policy the user is referring to. In the case where a user is providing
                # a templateName and we are here, ignore the policy.
                if policy.get("policyId", None) is not None:
                    if policy not in self.diff_modify:
                        self.changed_dict[0]["merged"].append(policy)
                        self.diff_modify.append(policy)
                else:
                    # User has provided a template name and a policy with such a template already exists. Since
                    # the user has provided a template name, we assume he is trying to create additional policies
                    # with the same template and hence create the policy
                    if policy not in self.diff_create:
                        self.changed_dict[0]["merged"].append(policy)
                        self.diff_create.append(policy)
                        policy_id = None
            elif rc == "DCNM_POLICY_DONT_ADD":
                # A policy exists and there is no difference between the one that exists and the one that is
                # is requested to be created. Check the 'create_additional_policy' flag and create it if it is
                # set to True
                if policy["create_additional_policy"] is True:

                    # Check if policy is being created using policy ID. In such a case since we are trying to create
                    # and additional policy here, clear the "id" and "policyId" fields. Otherwise CREATE will fail
                    # complaining the policy being created is not unique since a policy with the same policy number
                    # already exists

                    if "POLICY-" in policy.get("policyId", ""):
                        policy.pop("id")
                        policy.pop("policyId")
                        policy["policy_id_given"] = False

                    self.changed_dict[0]["merged"].append(policy)
                    self.diff_create.append(policy)
                    policy_id = None

            # Check the 'deploy' flag and decide if this policy is to be deployed
            if self.deploy is True:
                if (policy_id is not None) and (
                    policy_id not in self.deploy_payload
                ):
                    self.deploy_payload.append(policy_id)
                    deploy = {}
                    deploy["name"] = policy["templateName"]
                    deploy["serialNo"] = policy["serialNumber"]
                    deploy["policyId"] = policy_id
                    self.changed_dict[0]["deploy"].append(deploy)

    def dcnm_policy_get_delete_payload(self, policy):

        payload = {
            "id": int(policy["policyId"].split("-")[1]),
            "source": "",
            "serialNumber": policy["serialNumber"],
            "policyId": policy["policyId"],
            "entityType": "SWITCH",
            "entityName": "SWITCH",
            "templateName": policy["templateName"],
            "priority": -500,
            "nvPairs": {"FABRIC_NAME": "mmudigon"},
            "deleted": "true",
            "modifiedOn": 0,
        }

        for var in policy["nvPairs"]:
            payload["nvPairs"][var] = policy["nvPairs"][var]
        return payload

    def dcnm_policy_get_diff_deleted(self):

        # Delete playbook will only contain template names. But we need policy name to delete a
        # policy. So Get all policies from the list of switches provided and match the policies with
        # the given template names. Delete all matching policies

        # Get all the snos as a string separated by ','
        snos = self.dcnm_policy_get_snos_string(self.want)

        # Policies cannot be obtained by using template names. Policies have 'policy-id' which is the key
        # to get a policy. Since playbook includes only template names, we need to get all policies from
        # all the switches included in playbook, and then filter them out using template names.
        plist = self.dcnm_policy_get_all_policies(snos)

        # Filter the list of policies and keep only those that are matching. For delete case, playbook policies
        # may either contain template names of policy names. So compare both.
        match_pol = [
            pl
            for pl in plist
            for wp in self.want
            if (
                (wp["policy_id_given"] is False)
                and (pl["templateName"] == wp["templateName"])
                or (wp["policy_id_given"] is True)
                and (pl["policyId"] == wp["policyId"])
            )
        ]

        # match_pol contains all the policies which exist and are to be deleted
        # Build the delete payloads

        for pol in match_pol:

            del_payload = self.dcnm_policy_get_delete_payload(pol)
            if del_payload not in self.diff_delete:
                self.diff_delete.append(del_payload)
                self.changed_dict[0]["deleted"].append(
                    {
                        "policy": pol["policyId"],
                        "templateName": pol["templateName"],
                    }
                )

    def dcnm_policy_get_diff_query(self):

        # There are 3 different cases for query case:
        # 1. template name or policy id not given
        #    In this case we need to fetch all the policies from the specified switches.
        #
        # 2. template name given
        #    In this case we need to get all the policies from the specified switches. Filter these policies
        #    based on the given template name
        #
        # 3. policy id given
        #    In this case directly fetch the policy information from the specified switches

        snos = ""
        get_specific_policies = False
        match_templates = []
        match_pol = []
        for cfg in self.config:
            if cfg.get("switch", None) is not None:
                for sw_dict in cfg["switch"]:
                    if self.ip_sn[sw_dict["ip"]] not in snos:
                        if snos != "":
                            snos = snos + ","
                        snos = snos + self.ip_sn[sw_dict["ip"]]
            elif "POLICY-" in cfg["name"]:
                get_specific_policies = True
                # Policy ID is given, Fetch the specific information.
                pinfo = self.dcnm_policy_get_policy_info_from_dcnm(cfg["name"])
                if pinfo != []:
                    if (
                        pinfo["templateName"]
                        not in self.changed_dict[0]["query"]
                    ):
                        self.changed_dict[0]["query"].append(
                            pinfo["templateName"]
                        )
                    self.result["response"].append(pinfo)
            else:
                # templateName is given. Note this down
                match_templates.append(cfg["name"])

        if (get_specific_policies is False) or (match_templates != []):

            # Policies cannot be obtained by using template names. Policies have 'policy-id' which is the key
            # to get a policy. Since playbook includes only template names, we need to get all policies from
            # all the switches included in playbook, and then filter them out using template names.
            plist = self.dcnm_policy_get_all_policies(snos)

            if match_templates != []:
                # Filter the list of policies and keep only those that are matching. For delete case, playbook policies
                # may either contain template names of policy names. So compare both.
                match_pol = [
                    pl
                    for pl in plist
                    for mt_name in match_templates
                    if (pl["templateName"] == mt_name)
                ]
            else:
                match_pol = plist

        if match_pol:
            # match_pol contains all the policies which exist and match the given templates
            self.changed_dict[0]["query"].extend(
                list(
                    set(
                        [
                            t["templateName"]
                            for t in match_pol
                            if (
                                t["templateName"]
                                not in self.changed_dict[0]["query"]
                            )
                        ]
                    )
                )
            )
            self.result["response"].extend(match_pol)

    def dcnm_policy_create_policy(self, policy, command):

        path = self.paths["POLICY_BULK_CREATE"]

        json_payload = json.dumps(policy)

        retries = 0
        while retries < 3:
            resp = dcnm_send(self.module, command, path, json_payload)

            if (
                (resp.get("DATA", None) is not None)
                and (isinstance(resp["DATA"], dict))
                and (resp["DATA"].get("failureList", None) is not None)
            ):
                if isinstance(resp["DATA"]["failureList"], list):
                    fl = resp["DATA"]["failureList"][0]
                else:
                    fl = resp["DATA"]["failureList"]

                if "is not unique" in fl.get("message", ""):
                    retries = retries + 1
                    continue
            break

        self.result["response"].append(resp)

        return resp

    def dcnm_policy_delete_policy(self, policy, mark_del):

        if mark_del is True:
            path = self.paths["POLICY_MARK_DELETE"].format(policy["policyId"])
            json_payload = ""
            command = "PUT"
        else:
            path = self.paths["POLICY_WITH_POLICY_ID"].format(policy)
            json_payload = ""
            command = "DELETE"

        resp = dcnm_send(self.module, command, path, json_payload)
        return resp

    def dcnm_policy_deploy_policy(self, policy):

        path = self.paths["POLICY_DEPLOY"]

        json_payload = json.dumps(policy)

        resp = dcnm_send(self.module, "POST", path, json_payload)
        self.result["response"].append(resp)

        return resp

    def dcnm_policy_deploy_to_switches(self, snos):

        deploy_path = self.paths["POLICY_CFG_DEPLOY"].format(self.fabric)

        switches = ",".join(snos)
        deploy_path = deploy_path + switches

        resp = dcnm_send(self.module, "POST", deploy_path, "")
        self.result["response"].append(resp)

        return resp

    def dcnm_policy_send_message_to_dcnm(self):

        resp = None
        mark_delete_flag = False
        delete_flag = False
        create_flag = False
        deploy_flag = False
        snos = []
        delete = []

        for policy in self.diff_delete:

            # Get all serial numbers. We will require this to do save and deploy
            if policy["serialNumber"] not in snos:
                # Add the serial number only if the switch is managable.
                if policy["serialNumber"] in self.managable:
                    snos.append(policy["serialNumber"])

            # First Mark the policy as deleted. Then deploy the same to remove the configuration
            # from the switch. Then we can finally delete the policies from the DCNM server
            resp = self.dcnm_policy_delete_policy(policy, True)

            if isinstance(resp, list):
                resp = resp[0]
            if (
                resp
                and (resp.get("DATA", None) is not None)
                and (resp["RETURN_CODE"] == 200)
                and resp["MESSAGE"] == "OK"
            ):
                delete.append(policy["policyId"])
                mark_delete_flag = True
                self.result["response"].append(resp)
            else:
                self.result["response"].append(resp)
                self.module.fail_json(msg=resp)

        # Even for delete cases check the deploy flag and proceed
        if self.deploy is True:
            # Once all policies are deleted, do a switch level deploy so that the deleted policies are removed from the
            # switch
            if (snos != []) and (mark_delete_flag is True):

                # make a copy of snos. We will be updating snos in the following loop. But snos will be required
                # further down
                del_snos = snos.copy()
                retries = 0
                while retries < 50:

                    retries += 1
                    resp = self.dcnm_policy_deploy_to_switches(del_snos)

                    if resp and (resp["RETURN_CODE"] != 200):
                        self.module.fail_json(msg=resp)

                    # Get the SYNC status of the switch. After deploy, the status
                    # MUST be "In-Sync". If not keep retrying
                    path = self.paths["CONFIG_PREVIEW"].format(self.fabric)
                    path = (
                        path
                        + ",".join(del_snos)
                        + "?forceShowRun=false&showBrief=true"
                    )

                    cp_resp = dcnm_send(self.module, "GET", path, "")

                    if cp_resp.get("RETURN_CODE", 0) == 200:
                        match_data = [
                            item
                            for item in cp_resp.get("DATA", [])
                            if item["switchId"] in del_snos
                        ]
                    else:
                        self.module.fail_json(msg=cp_resp)

                    retry = False
                    for item in match_data:
                        if item["status"].lower() != "in-sync":
                            retry = True
                        else:
                            # remove the sno which is in "in-sync" from del_snos list
                            del_snos.remove(item["switchId"])
                    if retry:
                        time.sleep(1)
                    else:
                        break

            # Now use 'DELETE' command to delete the policies on the DCNM server
            for ditem in delete:
                # First check if the policy to be deleted exist.
                path = self.paths["POLICY_WITH_POLICY_ID"].format(ditem)

                resp = dcnm_send(self.module, "GET", path, "")

                if resp and isinstance(resp, list):
                    resp = resp[0]
                if (
                    resp
                    and (resp.get("DATA", None) is not None)
                    and (resp["RETURN_CODE"] == 200)
                    and resp["MESSAGE"] == "OK"
                ):
                    resp = self.dcnm_policy_delete_policy(ditem, False)

                    if isinstance(resp, list):
                        resp = resp[0]
                    if (
                        resp
                        and (resp.get("DATA", None) is not None)
                        and (resp["RETURN_CODE"] == 200)
                        and resp["MESSAGE"] == "OK"
                    ):
                        if "Deleted successfully" in resp["DATA"]["message"]:
                            delete_flag = True
                            self.result["response"].append(resp)

        for policy in self.diff_create:
            # POP the 'create_additional_policy' object before sending create
            policy.pop("create_additional_policy")
            policy.pop("policy_id_given")

            resp = self.dcnm_policy_create_policy(policy, "POST")

            if isinstance(resp, list):
                resp = resp[0]
            if (
                resp
                and (resp["RETURN_CODE"] == 200)
                and (resp["MESSAGE"] == "OK")
                and (resp.get("DATA", None) is not None)
            ):
                if resp["DATA"].get("successList", None) is not None:
                    if (
                        resp["DATA"]["successList"][0].get("status").lower()
                        == "success"
                    ):
                        policy_id = re.findall(
                            r"POLICY-\d+",
                            resp["DATA"]["successList"][0].get("message"),
                        )
                        if (self.deploy is True) and (
                            policy_id[0] not in self.deploy_payload
                        ):
                            self.deploy_payload.append(policy_id[0])
                            deploy = {}
                            deploy["name"] = policy["templateName"]
                            deploy["serialNo"] = policy["serialNumber"]
                            deploy["policyId"] = policy_id[0]
                            if deploy not in self.changed_dict[0]["deploy"]:
                                self.changed_dict[0]["deploy"].append(deploy)
                        create_flag = True
            else:
                self.module.fail_json(msg=resp)

        for policy in self.diff_modify:
            # POP the 'create_additional_policy' object before sending create
            policy.pop("create_additional_policy")
            resp = self.dcnm_policy_create_policy(policy, "PUT")
            if isinstance(resp, list):
                resp = resp[0]
            if (
                resp
                and (resp["RETURN_CODE"] == 200)
                and (resp["MESSAGE"] == "OK")
                and (resp.get("DATA", None) is not None)
            ):
                create_flag = True
            else:
                self.module.fail_json(msg=resp)

        if self.deploy_payload:
            resp = self.dcnm_policy_deploy_policy(self.deploy_payload)
            if isinstance(resp, list):
                resp = resp[0]
            if (
                resp
                and (resp["RETURN_CODE"] == 200)
                and (resp["MESSAGE"] == "OK")
                and (resp.get("DATA", None) is not None)
            ):
                deploy_flag = True
            else:
                self.module.fail_json(msg=resp)

        self.result["changed"] = (
            mark_delete_flag or delete_flag or create_flag or deploy_flag
        )

    def dcnm_translate_switch_info(self, config, ip_sn, hn_sn):

        if None is config:
            return

        for cfg in config:

            index = 0

            if None is cfg.get("switch", None):
                continue
            for sw_elem in cfg["switch"]:
                addr_info = dcnm_get_ip_addr_info(
                    self.module, sw_elem["ip"], ip_sn, hn_sn
                )
                cfg["switch"][index]["ip"] = addr_info
                index = index + 1

    def dcnm_translate_config(self, config):

        # In the playbook, switches is given as a separate object at policy configuration level.
        # We will remove it from there and add it to individual policies

        # Get the position of the matching dict
        pos = next(
            (index for (index, d) in enumerate(config) if "switch" in d), None
        )

        if pos is None:
            return config

        sw_dict = config.pop(pos)

        # 'switches' contains the switches related configuration items from playbook. Process these
        # and add the same to individual policy items as appropriate

        override_config = []
        for sw in sw_dict["switch"]:

            # Check if policies are included in the switch config. If so these policies will override
            # all other polcy configs given in the playbook globally. If not the switch can be included
            # in all individaul policy items

            if sw.get("policies", None) is not None:

                # 'policies are specified at switch level. Add each of these policies to 'config' object
                # along with the switch information

                for pol in sw["policies"]:

                    if pol.get("switch", None) is None:
                        pol["switch"] = []
                    if sw["ip"] not in pol["switch"]:
                        pol["switch"].append(sw["ip"])

                    override_config.append(pol)

            for cfg in config:

                if cfg.get("switch", None) is None:
                    cfg["switch"] = []
                if sw["ip"] not in cfg["switch"]:
                    cfg["switch"].append(sw["ip"])

        if config:
            updated_config = []
            for ovr_cfg in override_config:
                for cfg in config:
                    if cfg["name"] == ovr_cfg["name"]:
                        # Have a matching policy in config which is overridden by a more specifc policy under 'switch'
                        # Compare the switches under override policy with the switches in gobal config, and remove those switches from
                        # global config if present.
                        for sw in ovr_cfg["switch"]:
                            if sw in cfg["switch"]:
                                cfg["switch"].remove(sw)
                    if ovr_cfg not in updated_config:
                        updated_config.append(ovr_cfg)
            # Now go over the global config list, and add those cpolicies which have a non empty 'switch' list.
            for cfg in config:
                if cfg["switch"] != []:
                    updated_config.append(cfg)
            config = updated_config
        else:
            config = override_config

        return config


def main():

    """main entry point for module execution"""
    element_spec = dict(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict"),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "query"],
        ),
        deploy=dict(required=False, type="bool", default=True),
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    dcnm_policy = DcnmPolicy(module)

    # Note down the global 'deploy' status. We will have to check this and the local 'deploy' flags
    # included with individual policies to decide if a policy is to be deployed or not.
    dcnm_policy.deploy = module.params["deploy"]

    if not dcnm_policy.ip_sn:
        dcnm_policy.result[
            "msg"
        ] = "Fabric {0} missing on DCNM or does not have any switches".format(
            dcnm_policy.fabric
        )
        module.fail_json(
            msg="Fabric {0} missing on DCNM or does not have any switches".format(
                dcnm_policy.fabric
            )
        )

    state = module.params["state"]

    if not dcnm_policy.config:
        if state == "merged" or state == "deleted" or state == "query":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_policy.config
                )
            )

    # Convert all hostnames and domain names to IP addresses
    dcnm_policy.dcnm_translate_switch_info(
        dcnm_policy.config, dcnm_policy.ip_sn, dcnm_policy.hn_sn
    )

    if module.params["state"] != "query":
        # Translate the given playbook config to some convenient format. Each policy should
        # have the switches to be deployed.

        dcnm_policy.config = dcnm_policy.dcnm_translate_config(
            dcnm_policy.config
        )

        # See if this is required
        dcnm_policy.dcnm_policy_copy_config()
        dcnm_policy.dcnm_policy_validate_input()

        dcnm_policy.dcnm_policy_get_want()
        dcnm_policy.dcnm_policy_get_have()

    if module.params["state"] == "merged":
        dcnm_policy.dcnm_policy_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_policy.dcnm_policy_get_diff_deleted()

    if module.params["state"] == "query":
        dcnm_policy.dcnm_policy_get_diff_query()

    dcnm_policy.result["diff"] = dcnm_policy.changed_dict

    if (
        dcnm_policy.diff_create
        or dcnm_policy.diff_modify
        or dcnm_policy.deploy_payload
        or dcnm_policy.diff_delete
    ):
        dcnm_policy.result["changed"] = True
    else:
        module.exit_json(**dcnm_policy.result)

    if module.check_mode:
        dcnm_policy.result["changed"] = False
        module.exit_json(**dcnm_policy.result)

    dcnm_policy.dcnm_policy_send_message_to_dcnm()

    module.exit_json(**dcnm_policy.result)


if __name__ == "__main__":
    main()
