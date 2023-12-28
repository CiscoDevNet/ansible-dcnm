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
from typing import Any, Dict, List

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_merge_defaults import \
    ParamsMergeDefaults
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.mock_ansible_module import \
#     MockAnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies

from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.params_spec import \
    ParamsSpec
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.payload import \
    Config2Payload

def json_pretty(msg):
    return json.dumps(msg, indent=4, sort_keys=True)

class Task(ImagePolicyCommon):
    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.debug = True
        self.logfile = "/tmp/dcnm_image_policy.log"

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
        # policies which need to be created
        self.need_create = []
        # policies which need to be updated
        self.need_update = []
        self.validated_configs = []

        self.result = {"changed": False, "diff": [], "response": []}

    def get_have(self) -> None:
        """
        Caller: main()

        self.have consists of the current image policies on the controller
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.have = ImagePolicies(self.ansible_module)
        self.have.refresh()

    def get_want(self) -> None:
        """
        Caller: main()

        1. Validate the playbook configs
        2. Convert the validated configs to payloads
        3. Update self.want with this list of payloads
        """
        method_name = inspect.stack()[0][3]

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

        # convert the validated configs to payloads to more easily
        # compare them to self.have (which consists of the current
        # image policies on the controller).
        for config in self.validated_configs:
            payload = Config2Payload(self.ansible_module)
            payload.config = config
            payload.commit()
            self.want.append(payload.payload)

        # Exit if there's nothing to do
        if len(self.want) == 0:
            self.result["changed"] = False
            self.ansible_module.exit_json(**self.result)

    def get_need_merged(self) -> None:
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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        # new policies to be created
        need_create: List[Dict] = []
        # existing policies to be updated
        need_update: List[Dict] = []

        for want in self.want:
            self.have.policy_name = want.get("policyName")

            # Policy does not exist on the controller.
            if self.have.policy is None:
                need_create.append(copy.deepcopy(want))
                continue

            # The policy exists on the controller.  Merge
            # our want parameters with the controller's parameters
            # and add the merged parameters to the need_update list
            # if they differ from the want parameters.
            have = copy.deepcopy(self.have.policy)
            merged, needs_update = self._merge_policies(have, want)

            if needs_update is True:
                need_update.append(copy.deepcopy(merged))
        self.need_create = copy.copy(need_create)
        self.need_update = copy.copy(need_update)


    def get_need_merged_orig(self) -> None:
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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        # new policies to be created
        need_create: List[Dict] = []
        # existing policies to be updated
        need_update: List[Dict] = []

        for want in self.want:
            self.have.policy_name = want.get("policyName")

            if self.have.policy is not None:
                # If the policy exists on the controller, merge
                # our want parameters with the controller's parameters
                # and add the merged parameters to the need_update list
                # if they differ from the want parameters.
                have = copy.deepcopy(self.have.policy)
                merged, needs_update = self._merge_policies(have, want)

                if needs_update is True:
                    need_update.append(copy.deepcopy(merged))
                continue
            need_create.append(copy.deepcopy(want))
        self.need_create = copy.copy(need_create)
        self.need_update = copy.copy(need_update)

    def _merge_policies(self, have: Dict, want: Dict) -> Dict:
        """
        Merge the parameters in want with the parameters in have.

        We need to alter some items in have before we can compare it.
        Specifically:

        1.  The controller returns "N9K/N3K" for the platform, but
            it expects "N9K" in the payload.  We change "N9K/N3K"
            to "N9K" in have so that the compare works.
        2.  Remove fields in "have" that are not part of a request
            payload i.e. imageName and ref_count.
        2.  Remove all fields that are not set in "have"
        """
        method_name = inspect.stack()[0][3]

        # Remove keys that the controller adds which are not part
        # of a request payload.
        have.pop("imageName", None)
        have.pop("ref_count", None)
        have.pop("platformPolicies", None)

        # Change "N9K/N3K" to "N9K" in have so that it matches
        # the request payload.
        if have.get("platform", None) == "N9K/N3K":
            have["platform"] = "N9K"

        # Remove all keys that are not set
        if have.get("rpmimages", None) is None:
            have.pop("rpmimages", None)
        if have.get("packageName", None) == "":
            have.pop("packageName", None)

        # Merge the parameters in want with the parameters in have
        # with the parameters in want taking precedence.
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
        send the payloads to the controller that need to be created
        """
        method_name = inspect.stack()[0][3]

        if len(self.need_create) == 0:
            return

        path = self.endpoints.policy_create.get("path")
        verb = self.endpoints.policy_create.get("verb")

        requests_ok = []
        requests_nok = []
        for payload in self.need_create:
            response = dcnm_send(self.ansible_module, verb, path,
                                 data=json.dumps(payload))
            result = self._handle_response(response, verb)

            if not result["success"]:
                requests_nok.append(payload)
            else:
                requests_ok.append(payload)

        # all requests succeeded
        if len(requests_ok) == len(self.need_create):
            self.result["changed"] = True
            return

        # Some requests failed.  If at least one request succeeded,
        # set changed to True
        if len(requests_nok) != len(self.need_create):
            self.result["changed"] = True
        self._failure(response)


    def send_need_update(self) -> None:
        """
        send the payloads to the controller that need to be updated
        """
        method_name = inspect.stack()[0][3]

        if len(self.need_update) == 0:
            return

        path = self.endpoints.policy_edit.get("path")
        verb = self.endpoints.policy_edit.get("verb")

        requests_ok = []
        requests_nok = []
        for payload in self.need_update:
            response = dcnm_send(self.ansible_module, verb, path,
                                 data=json.dumps(payload))
            result = self._handle_response(response, verb)
            if not result["success"]:
                requests_nok.append(payload)
            else:
                requests_ok.append(payload)

        # All requests succeeded
        if len(requests_ok) == len(self.need_update):
            self.result["changed"] = True
            return

        # Some requests failed.  If at least one request succeeded,
        # set changed to True
        if len(requests_nok) != len(self.need_update):
            self.result["changed"] = True
        self._failure(response)


    def _failure(self, response) -> None:
        """
        fail_json with the response
        """
        msg = f"{self.class_name}._failure: "
        msg += f"response: {json_pretty(response)}"
        self.log.log_msg(msg)
        if not response.get("DATA"):
            self.module.fail_json(response)
        data = response.get("DATA", {})
        if response.get("DATA", {}).get("stackTrace", None):
            data.update(
                {"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"}
            )
        response.update({"DATA": data})
        self.module.fail_json(response)

    def build_payloads(self) -> None:
        """
        generate the payloads for each image policy

        We're not using this method since have and need
        are both in the format of a payload already.
        """
        payloads = []
        for config in self.validated_configs:
            payload = Config2Payload(self.ansible_module)
            payload.config = config
            payload.commit()
            payloads.append(payload.payload)
            msg = f"payload: {json_pretty(payload.payload)}"
            self.log.log_msg(msg)


parameters = dict()
parameters["name"] = "NR3F"
parameters["agnostic"] = False
parameters["description"] = "image policy of 10.3(3)F"
parameters["platform"] = "N9K"
parameters["release"] = "10.3.1_nxos64-cs_64bit"
parameters["packages"] = {}
parameters["packages"]["install"] = []
parameters["packages"]["install"].append("mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm")
parameters["packages"]["install"].append("some-other-package-install")
parameters["packages"]["uninstall"] = []
parameters["packages"]["uninstall"].append("mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000")
parameters["packages"]["uninstall"].append("some-other-package-uninstall")
parameters["epld_image"] = "n9000-epld.10.3.2.F.img"
parameters["disabled_rpm"] = ""


def main():
    element_spec = {
        "config": {"required": True, "type": "list"},
        "state": {"default": "merged", "choices": ["merged", "deleted", "query"]},
    }
    ansible_module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    # ansible_module.state = "merged"
    # ansible_module.config = parameters

    task_module = Task(ansible_module)
    task_module.get_want()
    task_module.get_have()
    task_module.get_need_merged()
    task_module.send_need_create()
    task_module.send_need_update()
    ansible_module.exit_json(**task_module.result)

if __name__ == "__main__":
    main()
