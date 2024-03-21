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
# pylint: disable=wrong-import-position
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

DOCUMENTATION = """
---
module: dcnm_image_policy
short_description: Image policy management for Nexus Dashboard Fabric Controller
version_added: "3.5.0"
description:
    - Create, delete, modify image policies.
author: Allen Robel (@quantumonion)
options:
    state:
        description:
            - The state of the feature or object after module completion
        type: str
        choices:
            - deleted
            - merged
            - overridden
            - query
            - replaced
        default: merged

    config:
        description:
            - List of dictionaries containing image policy parameters
        type: list
        elements: dict
        required: true
        suboptions:
            name:
                description:
                    - The image policy name.
                type: str
                required: true
            agnostic:
                description:
                    - The agnostic flag.
                type: bool
                default: false
                required: false
            description:
                description:
                    - The image policy description.
                type: str
                default: ""
                required: false
            epld_image:
                description:
                    - The epld image name.
                type: str
                default: ""
                required: false
            packages:
                description:
                    - A dictionary containing two keys, install and uninstall.
                type: dict
                required: false
                suboptions:
                    install:
                        description:
                            - A list of packages to install.
                        type: list
                        elements: str
                        required: false
                    uninstall:
                        description:
                            - A list of packages to uninstall.
                        type: list
                        elements: str
                        required: false
            platform:
                description:
                    - The platform to which the image policy applies e.g. N9K.
                type: str
                required: true
            release:
                description:
                    - The release associated with the image policy.
                    - This is derived from the image name as follows.
                    - From image name nxos64-cs.10.2.5.M.bin
                    - we need to extract version (10.2.5), platform (nxos64-cs), and bits (64bit).
                    - The release string conforms to format (version)_(platform)_(bits)
                    - so the resulting release string will be 10.2.5_nxos64-cs_64bit
                type: str
                required: true
            type:
                description:
                    - The type of the image policy e.g. PLATFORM.
                type: str
                default: PLATFORM
                required: false
"""

EXAMPLES = """
# This module supports the following states:
#
# deleted:
#   Delete image policies from the controller.
#
#   If an image policy has references (i.e. it is attached to a device),
#   the module will fail.  Use dcnm_image_upgrade module, state deleted,
#    to detach the image policy from all devices before deleting it.
#
# merged:
#   Create (or update) one or more image policies.
#
#   If an image policy does not exist on the controller, create it.
#   If an image policy already exists on the controller, edit it.
#
# overridden:
#   Create/delete one or more image policies.
#
#   If an image policy already exists on the controller, delete it and update
#   it with the configuration in the playbook task.
#
#   Remove any image policies from the controller that are not in the
#   playbook task.
#
# query:
#
#   Return the configuration for one or more image policies.
#
# replaced:
#
#   Replace image policies on the controller with policies in the playbook task.
#
#   If an image policy exists on the controller, but not in the playbook task,
#   do not delete it or modify it.
#
# Delete two image policies from the controller.

    -   name: Delete Image policies
        cisco.dcnm.dcnm_image_policy:
            state: deleted
            config:
            -   name: KR5M
            -   name: NR3F
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Merge two image policies into the controller.

    -   name: Merge Image policies
        cisco.dcnm.dcnm_image_policy:
            state: merged
            config:
            -   name: KR5M
                agnostic: false
                description: KR5M
                epld_image: n9000-epld.10.2.5.M.img
                packages:
                   install:
                   - mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm
                   uninstall:
                   - mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000
                platform: N9K
                release: 10.2.5_nxos64-cs_64bit
                type: PLATFORM
            -   name: NR3F
                description: NR3F
                platform: N9K
                epld_image: n9000-epld.10.3.1.F.img
                release: 10.3.1_nxos64-cs_64bit
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Override all policies on the controller and replace them with
# the policies in the playbook task.  Any policies other than
# KR5M and NR3F are deleted from the controller.

    -   name: Override Image policies
        cisco.dcnm.dcnm_image_policy:
            state: overridden
            config:
            -   name: KR5M
                agnostic: false
                description: KR5M
                epld_image: n9000-epld.10.2.5.M.img
                platform: N9K
                release: 10.2.5_nxos64-cs_64bit
                type: PLATFORM
            -   name: NR3F
                description: NR3F
                platform: N9K
                epld_image: n9000-epld.10.2.5.M.img
                release: 10.3.1_nxos64-cs_64bit
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Query the controller for the policies in the playbook task.

    -   name: Query Image policies
        cisco.dcnm.dcnm_image_policy:
            state: query
            config:
            -   name: NR3F
            -   name: KR5M
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Replace any policies on the controller that are in the playbook task with
# the configuration given in the playbook task.  Policies not listed in the
# playbook task are not modified and are not deleted.

    -   name: Replace Image policies
        cisco.dcnm.dcnm_image_policy:
            state: replaced
            config:
            -   name: KR5M
                agnostic: false
                description: KR5M
                epld_image: n9000-epld.10.2.5.M.img
                platform: N9K
                release: 10.2.5_nxos64-cs_64bit
                type: PLATFORM
            -   name: NR3F
                description: Replaced NR3F
                platform: N9K
                epld_image: n9000-epld.10.3.1.F.img
                release: 10.3.1_nxos64-cs_64bit
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result
"""

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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.create import \
    ImagePolicyCreateBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.delete import \
    ImagePolicyDelete
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.params_spec import \
    ParamsSpec
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.payload import \
    Config2Payload
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.query import \
    ImagePolicyQuery
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.replace import \
    ImagePolicyReplaceBulk
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.update import \
    ImagePolicyUpdateBulk


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


class Common(ImagePolicyCommon):
    """
    Common methods for all states
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.state = self.ansible_module.params.get("state")
        if self.ansible_module.params.get("check_mode") is True:
            self.check_mode = True

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Common(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.endpoints = ApiEndpoints()

        self._implemented_states = set()
        self._valid_states = ["deleted", "merged", "overridden", "query", "replaced"]
        self._states_require_config = {"merged", "overridden", "replaced", "query"}

        self.params = ansible_module.params
        self.rest_send = RestSend(self.ansible_module)

        self.config = ansible_module.params.get("config")

        if self.state in self._states_require_config and not self.config:
            msg = f"'config' parameter is required for state {self.state}"
            self.ansible_module.fail_json(msg, **self.rest_send.failed_result)

        self.validated = []
        self.have = {}
        self.want = []
        self.query = []
        self.idempotent_want = None

        # policies to created
        self.need_create = []
        # policies to updated
        self.need_delete = []
        # policies to deleted
        self.need_update = []
        # policies to query
        self.need_query = []
        self.validated_configs = []

        self.build_properties()

    def build_properties(self):
        """
        self.properties holds property values for the class
        """
        self.properties["results"] = None

    def get_have(self) -> None:
        """
        Caller: main()

        self.have consists of the current image policies on the controller
        """
        self.log.debug("ENTERED")
        self.have = ImagePolicies(self.ansible_module)
        self.have.results = self.results
        self.have.refresh()

    def get_want(self) -> None:
        """
        Caller: main()

        1. Validate the playbook configs
        2. Convert the validated configs to payloads
        3. Update self.want with this list of payloads
        """
        msg = "ENTERED"
        self.log.debug(msg)
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
            self.ansible_module.exit_json(**self.results.ok_result)

    @property
    def results(self):
        return self.properties["results"]

    @results.setter
    def results(self, value):
        self.properties["results"] = value


class Replaced(Common):
    """
    Handle replaced state
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Replaced(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("replaced")

    def commit(self) -> None:
        """
        Replace all policies on the controller that are in want
        """
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()
        self.get_have()

        image_policy_replace = ImagePolicyReplaceBulk(self.ansible_module)
        image_policy_replace.results = self.results
        image_policy_replace.payloads = self.want
        image_policy_replace.commit()


class Deleted(Common):
    """
    Handle deleted state
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.image_policy_delete = ImagePolicyDelete(self.ansible_module)

        msg = "ENTERED Deleted(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("deleted")

    def commit(self) -> None:
        """
        If config is present, delete all policies in self.want that exist on the controller
        If config is not present, delete all policies on the controller
        """
        self.results.state = self.state
        self.results.check_mode = self.check_mode
        self.image_policy_delete.policy_names = self.get_policies_to_delete()
        self.image_policy_delete.results = self.results
        self.image_policy_delete.commit()

    def get_policies_to_delete(self) -> List[str]:
        """
        Return a list of policy names to delete

        -   In config is present, return list of image policy names
            in self.want that exist on the controller
        -   If config is not present, return list of all image policy
            names on the controller
        """
        if not self.config:
            self.get_have()
            return list(self.have.all_policies.keys())
        self.get_want()
        self.get_have()
        policy_names_to_delete = []
        for want in self.want:
            if want["policyName"] in self.have.all_policies:
                policy_names_to_delete.append(want["policyName"])
        return policy_names_to_delete


class Query(Common):
    """
    Handle query state
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("query")

    def commit(self) -> None:
        """
        1.  query the fabrics in self.want that exist on the controller
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()

        image_policy_query = ImagePolicyQuery(self.ansible_module)
        image_policy_query.results = self.results
        policy_names_to_query = []
        for want in self.want:
            policy_names_to_query.append(want["policyName"])
        image_policy_query.policy_names = policy_names_to_query
        image_policy_query.commit()


class Overridden(Common):
    """
    Handle overridden state
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Overridden(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._implemented_states.add("overridden")

    def commit(self) -> None:
        """
        1.  Delete all policies on the controller that are not in self.want
        2.  Instantiate Merged() and call Merged().commit()
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()
        self.get_have()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.want: {json_pretty(self.want)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.have.all_policies: {json_pretty(self.have.all_policies)}"
        self.log.debug(msg)

        self._delete_policies_not_in_want()
        task = Merged(self.ansible_module)
        task.results = self.results
        task.commit()

    def _delete_policies_not_in_want(self) -> None:
        """
        Delete all policies on the controller that are not in self.want

        Caller: handle_overridden_state()
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        want_policy_names = set()
        for want in self.want:
            want_policy_names.add(want["policyName"])

        policy_names_to_delete = []
        for policy_name in self.have.all_policies:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"policy_name: {policy_name}"
            self.log.debug(msg)
            if policy_name not in want_policy_names:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Appending to policy_names_to_delete: {policy_name}"
                self.log.debug(msg)
                policy_names_to_delete.append(policy_name)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"policy_names_to_delete: {policy_names_to_delete}"
        self.log.debug(msg)

        instance = ImagePolicyDelete(self.ansible_module)
        instance.results = self.results
        instance.policy_names = policy_names_to_delete
        instance.commit()


class Merged(Common):
    """
    Handle merged state
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        super().__init__(ansible_module)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = f"params: {json_pretty(self.ansible_module.params)}"
        self.log.debug(msg)
        if not ansible_module.params.get("config"):
            msg = f"playbook config is required for {self.state}"
            ansible_module.fail_json(msg, **self.results.failed_result)

        self.image_policy_create = ImagePolicyCreateBulk(self.ansible_module)
        self.image_policy_update = ImagePolicyUpdateBulk(self.ansible_module)

        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        # new policies to be created
        self.need_create: List[Dict] = []
        # existing policies to be updated
        self.need_update: List[Dict] = []

        self._implemented_states.add("merged")

    def get_need(self):
        """
        Caller: commit()

        Build self.need for merged state
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
        for want in self.want:
            self.have.policy_name = want.get("policyName")

            # Policy does not exist on the controller so needs to be created.
            if self.have.policy is None:
                self.need_create.append(copy.deepcopy(want))
                continue

            # The policy exists on the controller.  Merge want parameters with
            # the controller's parameters and add the merged parameters to the
            # need_update list if they differ from the want parameters.
            have = copy.deepcopy(self.have.policy)
            merged, needs_update = self._merge_policies(have, want)

            if needs_update is True:
                self.need_update.append(copy.deepcopy(merged))

    def commit(self) -> None:
        """
        Commit the merged state requests
        """
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()
        self.get_have()
        self.get_need()
        self.send_need_create()
        self.send_need_update()

    def _prepare_for_merge(self, have: Dict, want: Dict):
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

        Caller: self.commit()
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
        self.image_policy_create.results = self.results
        self.image_policy_create.payloads = self.need_create
        self.image_policy_create.commit()

    def send_need_update(self) -> None:
        """
        Update the policies in self.need_update

        Callers:
        - self.handle_merged_state()
        """
        self.image_policy_update.results = self.results
        self.image_policy_update.payloads = self.need_update
        self.image_policy_update.commit()


def main():
    """
    main entry point for module execution
    """

    element_spec = {
        "config": {
            "required": False,
            "type": "list",
            "elements": "dict",
            "default": [],
        },
        "state": {
            "default": "merged",
            "choices": ["deleted", "merged", "overridden", "query", "replaced"],
        },
    }
    ansible_module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    # Create the base/parent logger for the dcnm collection.
    # To enable logging, set enable_logging to True.
    # log.config can be either a dictionary, or a path to a JSON file
    # Both dictionary and JSON file formats must be conformant with
    # logging.config.dictConfig and must not log to the console.
    # For an example configuration, see:
    # $ANSIBLE_COLLECTIONS_PATH/cisco/dcnm/plugins/module_utils/common/logging_config.json
    enable_logging = False
    log = Log(ansible_module)
    if enable_logging is True:
        collection_path = (
            "/Users/arobel/repos/collections/ansible_collections/cisco/dcnm"
        )
        config_file = (
            f"{collection_path}/plugins/module_utils/common/logging_config.json"
        )
        log.config = config_file
    log.commit()

    results = Results()
    if ansible_module.params["state"] == "deleted":
        task = Deleted(ansible_module)
        task.results = results
        task.commit()
    elif ansible_module.params["state"] == "merged":
        task = Merged(ansible_module)
        task.results = results
        task.commit()
    elif ansible_module.params["state"] == "overridden":
        task = Overridden(ansible_module)
        task.results = results
        task.commit()
    elif ansible_module.params["state"] == "query":
        task = Query(ansible_module)
        task.results = results
        task.commit()
    elif ansible_module.params["state"] == "replaced":
        task = Replaced(ansible_module)
        task.results = results
        task.commit()
    else:
        msg = f"Unknown state {task.ansible_module.params['state']}"
        ansible_module.fail_json(msg)

    results.build_final_result()

    if True in results.failed:
        msg = "Module failed."
        ansible_module.fail_json(msg, **results.final_result)
    ansible_module.exit_json(**results.final_result)


if __name__ == "__main__":
    main()
