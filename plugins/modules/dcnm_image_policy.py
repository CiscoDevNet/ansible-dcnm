#!/usr/bin/env python
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
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging
from typing import Dict, List

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_merge_defaults import \
    ParamsMergeDefaults
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.common.result import \
    Result
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.mock_ansible_module import \
#     MockAnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.create import \
    ImagePolicyCreateBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.delete import \
    ImagePolicyDelete
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.params_spec import \
    ParamsSpec
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.payload import \
    Config2Payload
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.replace import \
    ImagePolicyReplaceBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.update import \
    ImagePolicyUpdateBulk


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


class ImagePolicyTask(ImagePolicyCommon):
    """
    Create, delete, query, replace, or update image policies
    """
    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImagePolicyTask()")

        self.endpoints = ApiEndpoints()
        self.have = None
        self.idempotent_want = None

        self.path = None
        self.verb = None

        self.config = ansible_module.params.get("config", {})

        if not isinstance(self.config, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "expected list type for self.config. "
            msg += f"got {type(self.config).__name__}"
            self.ansible_module.fail_json(msg)

        self.want = []
        self.need = []
        # policies to created
        self.need_create = []
        # policies to updated
        self.need_delete = []
        # policies to deleted
        self.need_update = []
        # policies to query
        self.need_query = []
        self.validated_configs = []

        self.result = Result(self.ansible_module)
        self.result.result["changed"] = False

    def get_have(self) -> None:
        """
        Caller: main()

        self.have consists of the current image policies on the controller
        """
        self.log.debug("ENTERED")
        self.have = ImagePolicies(self.ansible_module)
        self.have.refresh()

    def get_want(self) -> None:
        """
        Caller: main()

        1. Validate the playbook configs
        2. Convert the validated configs to payloads
        3. Update self.want with this list of payloads
        """
        self.log.debug("ENTERED")
        # Generate the params_spec used to validate the configs
        params_spec = ParamsSpec(self.ansible_module)
        params_spec.commit()

        # If a parameter is missing from the config, and it has a default
        # value, add it to the config.
        merged_configs = []
        merge_defaults = ParamsMergeDefaults(self.ansible_module)
        merge_defaults.params_spec = params_spec.params_spec
        for config in self.config:
            merge_defaults.parameters = config
            merge_defaults.commit()
            merged_configs.append(merge_defaults.merged_parameters)

        # validate the merged configs
        self.validated_configs = []
        validator = ParamsValidate(self.ansible_module)
        validator.params_spec = params_spec.params_spec
        for config in merged_configs:
            validator.parameters = config
            validator.commit()
            self.validated_configs.append(copy.deepcopy(validator.parameters))

        # convert the validated configs to payloads to more easily compare them
        # to self.have (the current image policies on the controller).
        for config in self.validated_configs:
            payload = Config2Payload(self.ansible_module)
            payload.config = config
            payload.commit()
            self.want.append(payload.payload)

        # Exit if there's nothing to do
        if len(self.want) == 0:
            self.result.changed = False
            self.ansible_module.exit_json(**self.result.result)

    def handle_replaced_state(self) -> None:
        """
        Replace all policies on the controller that are in want
        """
        replaced = ImagePolicyReplaceBulk(self.ansible_module)
        replaced.payloads = self.want
        replaced.commit()
        for diff in replaced.diff:
            self.result.replaced = diff

    def handle_deleted_state(self) -> None:
        """
        1.  Delete all policies in self.want that exist on the controller
        """
        delete = ImagePolicyDelete(self.ansible_module)
        policy_names_to_delete = []
        for want in self.want:
            if want["policyName"] in self.have.all_policies:
                policy_names_to_delete.append(want["policyName"])

        msg = f"policy_names_to_delete: {policy_names_to_delete}, "
        msg += f"type {type(policy_names_to_delete).__name__}"
        self.log.debug(msg)
        delete.policy_names = policy_names_to_delete
        delete.commit()
        for diff in delete.diff:
            self.result.deleted = diff

    def _delete_policies_not_in_want(self) -> None:
        """
        Delete all policies on the controller that are not in self.want

        Caller: handle_overridden_state()
        """
        want_policy_names = set()
        for want in self.want:
            want_policy_names.add(want["policyName"])

        policy_names_to_delete = []
        for have in self.have.all_policies:
            have_policy_name = have.get("policyName")
            if have_policy_name not in want_policy_names:
                policy_names_to_delete.append(have_policy_name)

        delete = ImagePolicyDelete(self.ansible_module)
        delete.policy_names = policy_names_to_delete
        delete.commit()

    def handle_query_state(self) -> None:
        """
        1.  query the policies in self.want that exist on the controller
        """
        for want in self.want:
            if want["policyName"] in self.have.all_policies:
                self.result.query = self.have.all_policies.get(want["policyName"])

    def handle_overridden_state(self) -> None:
        """
        1.  Delete all policies on the controller that are not in self.want
        2.  Call handle_merged_state()
        """
        self._delete_policies_not_in_want()
        self.handle_merged_state()

    def handle_merged_state(self) -> None:
        """
        1.  Populate self.need_create with items from self.want that are
            not in self.have
        2.  Populate self.need_update with updated policies.  We update
            policies as follows:
            a.  If a policy is in both self.want amd self.have, and they
                contain differences, merge self.want into self.have,
                with self.want keys taking precedence and append the
                merged policy to self.need_update.
            b.  If a policy is in both self.want and self.have, and they
                are identical, do not append the policy to self.need_update
                (i.e. do nothing).
        """
        # new policies to be created
        need_create: List[Dict] = []
        # existing policies to be updated
        need_update: List[Dict] = []

        for want in self.want:
            self.have.policy_name = want.get("policyName")

            # Policy does not exist on the controller so needs to be created.
            if self.have.policy is None:
                need_create.append(copy.deepcopy(want))
                continue

            # The policy exists on the controller.  Merge want parameters with
            # the controller's parameters and add the merged parameters to the
            # need_update list if they differ from the want parameters.
            have = copy.deepcopy(self.have.policy)
            merged, needs_update = self._merge_policies(have, want)

            if needs_update is True:
                need_update.append(copy.deepcopy(merged))
        self.need_create = copy.copy(need_create)
        self.need_update = copy.copy(need_update)
        self.send_need_create()
        self.send_need_update()

    def _prepare_for_merge(self, have: Dict, want: Dict) -> (Dict, Dict):
        """
        1.  Remove fields in "have" that are not part of a request payload i.e.
            imageName and ref_count.
        2.  The controller returns "N9K/N3K" for the platform, but it expects
            "N9K" in the payload.  We change "N9K/N3K" to "N9K" in have so that
            the compare works.
        3.  Remove all fields that are not set in both "have" and "want"

        Caller: self._merge_policies()
        """
        # Remove keys that the controller adds which are not part
        # of a request payload.
        for key in ["imageName", "ref_count", "platformPolicies"]:
            have.pop(key, None)

        # Change "N9K/N3K" to "N9K" in have to match the request payload.
        if have.get("platform", None) == "N9K/N3K":
            have["platform"] = "N9K"

        # If keys are not set in both have and want, remove them.
        for key in ["agnostic", "epldImgName", "packageName", "rpmimages"]:
            if have.get(key, None) is None and want.get(key, None) is None:
                have.pop(key, None)
                want.pop(key, None)

            if have.get(key, None) == "" and want.get(key, None) == "":
                have.pop(key, None)
                want.pop(key, None)
        return (have, want)

    def _merge_policies(self, have: Dict, want: Dict) -> Dict:
        """
        Merge the parameters in want with the parameters in have.

        Caller: self.handle_merged_state()
        """
        (have, want) = self._prepare_for_merge(have, want)

        # Merge the parameters in want with the parameters in have.
        # The parameters in want take precedence.
        merge = MergeDicts(self.ansible_module)
        merge.dict1 = have
        merge.dict2 = want
        merge.commit()
        merged = copy.deepcopy(merge.dict_merged)

        needs_update = False

        if have != merged:
            needs_update = True

        return (merged, needs_update)

    def send_need_create(self) -> None:
        """
        Create the policies in self.need_create

        Callers:
        - self.handle_merged_state()
        """
        policy_create = ImagePolicyCreateBulk(self.ansible_module)
        policy_create.payloads = self.need_create
        policy_create.commit()
        for diff in policy_create.diff:
            self.result.merged = diff

    def send_need_update(self) -> None:
        """
        Update the policies in self.need_update

        Callers:
        - self.handle_merged_state()
        """
        bulk_update = ImagePolicyUpdateBulk(self.ansible_module)
        bulk_update.payloads = self.need_update
        bulk_update.commit()
        for diff in bulk_update.diff:
            self.result.merged = diff

    def _failure(self, response) -> None:
        """
        fail_json with the response
        """
        msg = f"{self.class_name}._failure: "
        msg += f"response: {json_pretty(response)}"
        self.log.error(msg)
        if not response.get("DATA"):
            self.ansible_module.fail_json(response)
        data = response.get("DATA", {})
        if response.get("DATA", {}).get("stackTrace", None):
            data.update(
                {"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"}
            )
        response.update({"DATA": data})
        self.ansible_module.fail_json(response, self.result.result)


# parameters = {}
# parameters["name"] = "NR3F"
# parameters["agnostic"] = False
# parameters["description"] = "image policy of 10.3(3)F"
# parameters["platform"] = "N9K"
# parameters["release"] = "10.3.1_nxos64-cs_64bit"
# parameters["packages"] = {}
# parameters["packages"]["install"] = []
# parameters["packages"]["install"].append("mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm")
# parameters["packages"]["install"].append("some-other-package-install")
# parameters["packages"]["uninstall"] = []
# parameters["packages"]["uninstall"].append(
#     "mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000"
# )
# parameters["packages"]["uninstall"].append("some-other-package-uninstall")
# parameters["epld_image"] = "n9000-epld.10.3.2.F.img"
# parameters["disabled_rpm"] = ""


def main():
    """
    main entry point for module execution
    """

    element_spec = {
        "config": {"required": True, "type": "list"},
        "state": {
            "default": "merged",
            "choices": ["deleted", "merged", "overridden", "query", "replaced"],
        },
    }
    ansible_module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    # Create the base/parent logger for the dcnm collection.
    # To disable logging, comment out log.config = <file_path> below
    # log.config can be either a dictionary, or a path to a JSON file
    # Both dictionary and JSON file formats must be conformant with
    # logging.config.dictConfig and must not log to the console.
    # For an example configuration, see:
    # $ANSIBLE_COLLECTIONS_PATH/cisco/dcnm/plugins/module_utils/common/logging_config.json
    log = Log(ansible_module)
    collection_path = "/Users/arobel/repos/collections/ansible_collections/cisco/dcnm"
    config_file = f"{collection_path}/plugins/module_utils/common/logging_config.json"
    log.config = config_file
    log.commit()

    task_module = ImagePolicyTask(ansible_module)
    task_module.get_want()
    task_module.get_have()
    if ansible_module.params["state"] == "deleted":
        task_module.handle_deleted_state()
    elif ansible_module.params["state"] == "merged":
        task_module.handle_merged_state()
    elif ansible_module.params["state"] == "overridden":
        task_module.handle_overridden_state()
    elif ansible_module.params["state"] == "query":
        task_module.handle_query_state()
    elif ansible_module.params["state"] == "replaced":
        task_module.handle_replaced_state()
    else:
        msg = f"Unknown state {task_module.ansible_module.params['state']}"
        task_module.ansible_module.fail_json(msg)

    ansible_module.exit_json(**task_module.result.result)


if __name__ == "__main__":
    main()
