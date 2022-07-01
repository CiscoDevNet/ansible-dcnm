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
module: dcnm_template
short_description: DCNM Ansible Module for managing templates.
version_added: "1.1.0"
description:
    - DCNM Ansible Module for creating, deleting and modifying template service
    - operations
author: Mallik Mudigonda(@mmudigon)
options:
  state:
    description:
    - The required state of the configuration after module completion.
    type: str
    choices:
      - merged
      - deleted
      - query
    default: merged

  config:
    description:
    - A dictionary of template operations
    type: list
    elements: dict
    required: true
    suboptions:
      name:
        description:
        - Name of the template.
        type: str

      description:
        description:
        - Description of the template. The description may include the details
          regarding the content
        type: str
        default: ''

      tags:
        description:
        - User defined labels for identifying the templates
        type: str
        default: ''

      content:
        description:
        - Multiple line configuration snip that can be used to associate to
          devices as policy
        type: str

      type:
        description:
        - Type of the template content either CLI or Python
        type: str
        choices:
          - cli
          - python
        default: cli
"""

EXAMPLES = """

# States:
# This module supports the following states:
#
# Merged:
#   Templates defined in the playbook will be merged into the target.
#
#   The templates listed in the playbook will be created if not already present on the DCNM
#   server. If the template is already present and the configuration information included
#   in the playbook is either different or not present in DCNM, then the corresponding
#   information is added to the template on DCNM. If a template mentioned in playbook
#   is already present on DCNM and there is no difference in configuration, no operation
#   will be performed for such a template.
#
# Deleted:
#   Templates defined in the playbook will be deleted from the target.
#
#   Deletes the list of templates specified in the playbook.
#
# Query:
#   Returns the current DCNM state for the templates listed in the playbook.


# To create or modify templates

- name: Create or modify templates
  cisco.dcnm.dcnm_template:
    state: merged        # only choose form [merged, deleted, query]
    config:
      - name: template_101
        description: "Template_101"
        tags: "internal policy 101"
        content: |
          telemetry
            certificate /bootflash/telegraf.crt telegraf
            destination-profile
              use-vrf management
            destination-group 101
              ip address 10.195.225.176 port 57101 protocol gRPC encoding GPB
            sensor-group 101
              data-source DME
              path sys/ch depth unbounded
            subscription 101
              dst-grp 101
              snsr-grp 101 sample-interval 10101

      - name: template_102
        description: "Template_102"
        tags: "internal policy 102"
        content: |
          telemetry
            certificate /bootflash/telegraf.crt telegraf
            destination-profile
              use-vrf management
            destination-group 1
              ip address 10.195.225.102 port 57102 protocol gRPC encoding GPB
            sensor-group 102
              data-source DME
              path sys/ch depth unbounded
            subscription 102
              dst-grp 102
              snsr-grp 102 sample-interval 10102

# To delete templates

- name: Delete templates
  cisco.dcnm.dcnm_template:
    state: deleted       # only choose form [merged, deleted, query]
    config:
      - name: template_101

      - name: template_102

      - name: template_103

      - name: template_104

# To query templates

- name: Query templates
  cisco.dcnm.dcnm_template:
    state: query       # only choose form [merged, deleted, query]
    config:
      - name: template_101

      - name: template_102

      - name: template_103

      - name: template_104
"""

import json
import re
import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
    dcnm_version_supported,
)


class DcnmTemplate:

    dcnm_template_paths = {
        11: {
            "TEMP_VALIDATE": "/rest/config/templates/validate",
            "TEMP_GET_SWITCHES": "/rest/control/policies/switches?serialNumber={}",
            "TEMP_GET_SW_ROLES": "/rest/control/switches/roles",
            "TEMPLATE": "/rest/config/templates/template",
            "TEMP_DELETE_BULK": "/rest/config/templates/delete/bulk",
            "TEMPLATE_WITH_NAME": "/rest/config/templates/{}",
        },
        12: {
            "TEMP_VALIDATE": "/appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates/validate",
            "TEMP_GET_SWITCHES": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/switches?serialNumber={}",
            "TEMP_GET_SW_ROLES": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/switches/roles",
            "TEMPLATE": "/appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates/template",
            "TEMP_DELETE_BULK": "/appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates/delete/bulk",
            "TEMPLATE_WITH_NAME": "/appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates/{}",
        },
    }

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.config = copy.deepcopy(module.params.get("config"))
        self.want = []
        self.have = []
        self.pb_input = []
        self.diff_create = []
        self.diff_delete = []
        self.diff_query = []
        self.valid_fail = []
        self.template_info = []
        self.fd = None
        self.changed_dict = [{"merged": [], "deleted": [], "query": [], "failed": []}]

        self.dcnm_version = dcnm_version_supported(self.module)

        self.result = dict(changed=False, diff=[], response=[])
        self.paths = self.dcnm_template_paths[self.dcnm_version]

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("template.log", "w+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.write("\n")
            self.fd.flush()

    def dcnm_template_validate_input(self):

        if self.config is None:
            self.module.fail_json(
                msg="config: parameter is required and cannot be empty"
            )

        if self.module.params["state"] == "merged":
            template_spec = dict(
                name=dict(required=True, type="str"),
                description=dict(required=False, type="str", default=""),
                tags=dict(required=False, type="str", default=""),
                content=dict(required=True, type="str"),
                type=dict(required=False, type="str", default="cli"),
            )
        elif self.module.params["state"] == "deleted":
            template_spec = dict(name=dict(required=True, type="str"))
        elif self.module.params["state"] == "query":
            template_spec = dict(name=dict(required=True, type="str"))

        template_info, invalid_params = validate_list_of_dicts(
            self.config, template_spec
        )
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        self.template_info.extend(template_info)

    def dcnm_template_get_template_info_from_dcnm(self, path, name):

        resp = dcnm_send(self.module, "GET", path)

        if (
            resp
            and resp["RETURN_CODE"] == 200
            and resp["MESSAGE"] == "OK"
            and resp["DATA"]
        ):
            if resp["DATA"]["name"] == name:
                return resp["DATA"]
        else:
            return []

    def dcnm_template_get_template_payload(self, ditem):

        if self.module.params["state"] == "merged":

            if ("template variables" not in ditem["content"]) and (
                "template content" not in ditem["content"]
            ):
                std_cont = "##template properties\nname = __TEMPLATE_NAME;\ndescription = __DESCRIPTION;\ntags = __TAGS;\nuserDefined = true;\nsupportedPlatforms = All;\ntemplateType = POLICY;\ntemplateSubType = DEVICE;\ncontentType = TEMPLATE_CLI;\nimplements = implements;\ndependencies = ;\npublished = false;\n##\n##template variables\n##\n##template content\n"  # noqa
            else:
                std_cont = "##template properties\nname = __TEMPLATE_NAME;\ndescription = __DESCRIPTION;\ntags = __TAGS;\nuserDefined = true;\nsupportedPlatforms = All;\ntemplateType = POLICY;\ntemplateSubType = DEVICE;\ncontentType = TEMPLATE_CLI;\nimplements = implements;\ndependencies = ;\npublished = false;\n"  # noqa

            template_payload = {}

            std_cont = std_cont.replace("__TEMPLATE_NAME", ditem["name"])
            std_cont = std_cont.replace("__DESCRIPTION", ditem["description"])
            std_cont = std_cont.replace("__TAGS", ditem["tags"])
            if ditem["type"] == "python":
                std_cont = std_cont.replace("TEMPLATE_CLI", "PYTHON")

            final_cont = std_cont + ditem["content"] + "##"

            template_payload["template_name"] = ditem["name"]
            template_payload["content"] = final_cont
        elif self.module.params["state"] == "deleted":
            template_payload = {"name": [], "fabTemplate": []}
            template_payload["name"] = ditem["name"]

        return template_payload

    def dcnm_template_compare_template(self, template):

        if self.have == []:
            return "DCNM_TEMPLATE_ADD_NEW"

        for have in self.have:

            update_content = False
            if template["template_name"] == have["name"]:

                # First the content in want must be updated based on what is given
                # and what is already existing. For 'merge', properties that are not
                # specified should be left as is and those which are different from
                # have must be updated.

                match_pb = [
                    t for t in self.pb_input if template["template_name"] == t["name"]
                ][0]

                if match_pb:
                    if match_pb.get("description", None) is None:
                        # Description is not included in config. So take it from have
                        desc = have["description"]
                        update_content = True
                    else:
                        desc = match_pb["description"]

                    if match_pb.get("tags", None) is None:
                        # Tags is not included in config. So take it from have
                        tags = have["tags"]
                        update_content = True
                    else:
                        tags = match_pb["tags"]

                    if match_pb.get("type", None) is None:
                        # Type is not included in config. So take it from have
                        type = have["contentType"].lower()
                        update_content = True
                    else:
                        type = match_pb["type"]

                    if update_content is True:
                        template["content"] = self.dcnm_template_build_content(
                            match_pb["content"],
                            template["template_name"],
                            desc,
                            tags,
                            type,
                        )
                # Check the content
                # Before doing that remove 'imports = ;\n' from have. We do not have it in want.

                have["content"] = have["content"].replace("imports = ;\n", "")

                # Also ignore difference in blank spaces.
                # have always adds an extra \n at the end. Remove that before you compare

                w = re.sub(" +", "", template["content"])
                h = re.sub(" +", "", have["content"]).rstrip("\n")

                if w != h:
                    return "DCNM_TEMPLATE_MERGE"
                else:
                    return "DCNM_TEMPLATE_DONT_ADD"

        return "DCNM_TEMPLATE_ADD_NEW"

    def dcnm_template_validate_template(self, template):

        path = self.paths["TEMP_VALIDATE"]

        resp = dcnm_send(self.module, "POST", path, template["content"], "text")

        if resp and resp["RETURN_CODE"] == 200 and resp["MESSAGE"] == "OK":
            # DATA may have multiple dicts with different reports. Check all reports and ignore warnings.
            # If there are errors, take it as validation failure

            # resp['DATA'] may be a list in case of templates with no parameters. But for templates
            # with parameters resp['DATA'] will be a dict directly with 'status' as 'Template Validation Successful'
            if isinstance(resp["DATA"], list):
                for d in resp["DATA"]:
                    if d.get("reportItemType", " ").lower() == "error":
                        self.result["response"].append(resp)
                        return 0
                return resp["RETURN_CODE"]
            elif isinstance(resp["DATA"], dict):
                if (
                    resp["DATA"].get("status", " ").lower()
                    != "template validation successful"
                ):
                    self.result["response"].append(resp)
                    return 0
                return resp["RETURN_CODE"]
            else:
                self.result["response"].append(resp)
                return 0
        else:
            return 0

    def dcnm_template_get_policy_list(self, snos, tlist):

        policies = {}
        path = self.paths["TEMP_GET_SWITCHES"].format(snos)

        resp = dcnm_send(self.module, "GET", path)

        if (
            resp
            and (resp["RETURN_CODE"] == 200)
            and (resp["MESSAGE"] == "OK")
            and resp["DATA"]
        ):
            for p in resp["DATA"]:
                if p["templateName"] in tlist:
                    if policies.get(p["templateName"], None) is None:
                        policies[p["templateName"]] = {}
                    policies[p["templateName"]][p["policyId"]] = {}
                    policies[p["templateName"]][p["policyId"]]["fabricName"] = p[
                        "fabricName"
                    ]
                    policies[p["templateName"]][p["policyId"]]["serialNumber"] = p[
                        "serialNumber"
                    ]

        return policies

    def dcnm_template_get_policies(self, tlist):

        policies = {}

        # We need to check all switches on the Server to see if the given templates are deployed
        # on any of the switches

        path = self.paths["TEMP_GET_SW_ROLES"]

        resp = dcnm_send(self.module, "GET", path)

        if (
            resp
            and (resp["RETURN_CODE"] == 200)
            and (resp["MESSAGE"] == "OK")
            and resp["DATA"]
        ):
            switches = resp["DATA"]

            snos = ""
            for sw in switches:
                # Build the string of serial numbers which will be used to fetch the policies from all the switches
                snos = snos + sw["serialNumber"] + ","

            snos.rstrip(",")
            policies = self.dcnm_template_get_policy_list(snos, tlist)
        return policies

    def dcnm_template_get_tlist_from_resp(self, resp):

        # Get the list of templates not deleted because they are in use.

        tstr = resp["DATA"].split("not deleted:")[1].replace("[", "").replace("]", "")
        tstr = tstr.replace(" ", "")
        template_list = tstr.split(",")

        return template_list

    def dcnm_template_create_template(self, template):

        payload = {}
        payload["content"] = template["content"]
        path = self.paths["TEMPLATE"]

        if self.dcnm_version == 12:
            payload["templatename"] = template["template_name"]
        json_payload = json.dumps(payload)

        resp = dcnm_send(self.module, "POST", path, json_payload)
        self.result["response"].append(resp)

        return resp

    def dcnm_template_delete_template(self, del_payload):

        tlist = []
        policies = {}
        path = self.paths["TEMP_DELETE_BULK"]
        changed = False

        json_payload = json.dumps(del_payload)

        resp = dcnm_send(self.module, "DELETE", path, json_payload)

        if "Template deletion successful" in resp["DATA"]:
            resp["DATA"] = resp["DATA"].replace("Invalid JSON response: ", "")
            changed = True
        elif "notDeletd" in resp["DATA"]:
            resp["DATA"] = resp["DATA"].replace("Invalid JSON response: ", "")
            resp["DATA"] = resp["DATA"].replace(
                '"notDeletdTemplate"', "Templates in use, not deleted"
            )

            tlist = self.dcnm_template_get_tlist_from_resp(resp)

            # Since there are templates which are not deleted because they are being used by some policies,
            # get the policies that are using these templates. This will help the user to take necessary actions

            policies = self.dcnm_template_get_policies(tlist)

            # Make sure to mark changed to False if none of the templates are deleted

            if len(del_payload["fabTemplate"]) == len(tlist):
                # Since the number of templates in tlist is same as the number of templates to be deleted, it means
                # no template has been deleted. Hence we can mark changed to False
                self.result["changed"] = False
            else:
                self.result["changed"] = True
        else:
            self.module.fail_json(msg=resp)

        if policies:
            self.result["template-policy-map"] = policies
        self.result["response"].append(resp)
        return changed

    def dcnm_template_get_have(self):

        # Go through the WANT list of templates. For each template get the
        # template information if it exists

        for template in self.want:

            if not self.want:
                return

            # payload in self.want will be different for merged and deleted states. So fetch the name
            # based on the state
            # Fetch the information from DCNM w.r.t to the template that we have in self.want

            if self.module.params["state"] == "merged":
                name = template["template_name"]
            elif self.module.params["state"] == "deleted":
                name = template["name"]

            path = self.paths["TEMPLATE_WITH_NAME"].format(name)
            template_payload = self.dcnm_template_get_template_info_from_dcnm(
                path, name
            )

            if template_payload:
                self.have.append(template_payload)

    def dcnm_template_get_want(self):

        for delem in self.template_info:
            template_payload = self.dcnm_template_get_template_payload(delem)
            if template_payload not in self.want:
                self.want.append(template_payload)

    def dcnm_template_get_diff_merge(self):

        self.diff_create = []
        self.diff_delete = []
        self.diff_query = []
        self.valid_fail = []

        if not self.want:
            return

        for template in self.want:
            rc = self.dcnm_template_validate_template(template)
            if rc == 0:
                self.changed_dict[0]["failed"].append(template)
            else:
                # Verify if the template is already present. If there is no change between what is
                # being requested and what is already present, ignore the same.
                rc = self.dcnm_template_compare_template(template)
                if rc != "DCNM_TEMPLATE_DONT_ADD":
                    self.changed_dict[0]["merged"].append(template)
                    self.diff_create.append(template)

    def dcnm_template_get_diff_deleted(self):

        self.diff_create = []
        self.diff_query = []
        self.diff_delete = []
        del_payload = {"name": [], "fabTemplate": []}

        for template in self.want:

            # Check if the template is present. If not ignore the request
            match_temp = [t for t in self.have if template["name"] == t["name"]]

            if match_temp:
                del_payload["fabTemplate"].append(template["name"])
                self.changed_dict[0]["deleted"].append(template["name"])
        if del_payload["fabTemplate"]:
            self.diff_delete.append(del_payload)

    def dcnm_template_get_diff_query(self):

        self.diff_create = []
        self.diff_query = []
        self.diff_delete = []
        tlist = []

        for template in self.template_info:

            path = self.paths["TEMPLATE_WITH_NAME"].format(template["name"])
            template_payload = self.dcnm_template_get_template_info_from_dcnm(
                path, template["name"]
            )

            if template_payload:
                self.diff_query.append(template_payload)
                self.changed_dict[0]["query"].append(template_payload["name"])
                self.result["response"].append(template_payload)
                tlist.append(template["name"])

        if tlist:
            policies = self.dcnm_template_get_policies(tlist)
            if policies:
                self.result["template-policy-map"] = policies

    def dcnm_template_send_message_to_dcnm(self):

        resp = None
        delete_flag = False
        create_flag = False

        # First process delete list
        if self.diff_delete:
            delete_flag = self.dcnm_template_delete_template(self.diff_delete[0])

        for template in self.diff_create:
            resp = self.dcnm_template_create_template(template)
            if isinstance(resp, list):
                resp = resp[0]
            if resp and resp["RETURN_CODE"] == 200:
                create_flag = True
            if resp and resp["RETURN_CODE"] >= 400:
                self.module.fail_json(msg=resp)

        self.result["changed"] = delete_flag or create_flag

    def dcnm_template_build_content(self, content, name, desc, tags, type):

        std_cont = "##template properties\nname = __TEMPLATE_NAME;\ndescription = __DESCRIPTION;\ntags = __TAGS;\nuserDefined = true;\nsupportedPlatforms = All;\ntemplateType = POLICY;\ntemplateSubType = DEVICE;\ncontentType = TEMPLATE_CLI;\nimplements = implements;\ndependencies = ;\npublished = false;\n##\n##template content\n"  # noqa

        std_cont = std_cont.replace("__TEMPLATE_NAME", name)
        std_cont = std_cont.replace("__DESCRIPTION", desc)
        std_cont = std_cont.replace("__TAGS", tags)
        if type == "python":
            std_cont = std_cont.replace("TEMPLATE_CLI", "PYTHON")

        final_cont = std_cont + content + "##"
        return final_cont

    # Flatten the incoming config database and have the required fileds updated.
    # This modified config DB will be used while creating payloads. To avoid
    # messing up the incoming config make a copy of it.
    def dcnm_template_copy_config(self):

        if None is self.config:
            return

        for cfg in self.config:
            # Default value is not filled automatically in dicts nested in list
            # Therefore handle defaulting type field of config list here
            if "type" not in cfg.keys():
                cfg["type"] = "cli"
            self.pb_input.append(copy.deepcopy(cfg))


def main():

    """main entry point for module execution"""
    element_spec = dict(
        config=dict(required=True, type="list", elements="dict"),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "query"],
        ),
    )

    module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    dcnm_template = DcnmTemplate(module)

    dcnm_template.dcnm_template_copy_config()
    dcnm_template.dcnm_template_validate_input()

    if module.params["state"] != "query":
        dcnm_template.dcnm_template_get_want()
        dcnm_template.dcnm_template_get_have()

    if module.params["state"] == "merged":
        dcnm_template.dcnm_template_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_template.dcnm_template_get_diff_deleted()

    if module.params["state"] == "query":
        dcnm_template.dcnm_template_get_diff_query()

    dcnm_template.result["diff"] = dcnm_template.changed_dict

    if dcnm_template.diff_create or dcnm_template.diff_delete:
        dcnm_template.result["changed"] = True
    else:
        module.exit_json(**dcnm_template.result)

    if module.check_mode:
        dcnm_template.result["changed"] = False
        module.exit_json(**dcnm_template.result)

    dcnm_template.dcnm_template_send_message_to_dcnm()

    module.exit_json(**dcnm_template.result)


if __name__ == "__main__":
    main()
