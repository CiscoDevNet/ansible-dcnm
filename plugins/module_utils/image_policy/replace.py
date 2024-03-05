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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class ImagePolicyReplaceBulk(ImagePolicyCommon):

    """
    Handle Ansible replaced state for image policies

    Given a list of payloads, bulk-replace the image policies therein.
    The payload format is given below.

    agnostic        bool(), optional. true or false
    epldImgName     str(), optional. name of an EPLD image to install.
    nxosVersion     str(), required. NX-OS version as version_type_arch
    packageName:    str(), optional, A comma-separated list of packages
    platform:       str(), optional, one of N9K, N6K, N5K, N3K
    policyDesc      str(), optional, description for the image policy
    policyName:     str(), required.  Name of the image policy.
    policyType      str(), required. PLATFORM or UMBRELLA
    rpmimages:      str(), optional. A comma-separated list of packages to uninstall

    Example (replacing two policies)):

    policies = [
        {
            "agnostic": false,
            "epldImgName": "n9000-epld.10.3.2.F.img",
            "nxosVersion": "10.3.1_nxos64-cs_64bit",
            "packageName": "mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm",
            "platform": "N9K",
            "policyDescr": "10.3(3)F",
            "policyName": "FOO",
            "policyType": "PLATFORM",
            "rpmimages": "mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000"
        },
        {
            "policyDescr": "new policy description for BAR",
            "policyName": "BAR,
        },
    ]
    bulk_replace = ImagePolicyReplaceBulk(ansible_module)
    bulk_replace.payloads = policies
    bulk_replace.commit()
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__
        self.check_mode = self.ansible_module.check_mode

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED ImagePolicyReplaceBulk(): "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.endpoints = ApiEndpoints()
        self._image_policies = ImagePolicies(self.ansible_module)

        self.action = "replace"
        self._payloads_to_commit = []
        self.response_ok = []
        self.response_nok = []
        self.result_ok = []
        self.result_nok = []
        self.diff_ok = []
        self.diff_nok = []

        self.path = self.endpoints.policy_edit.get("path")
        self.verb = self.endpoints.policy_edit.get("verb")

        self._mandatory_payload_keys = set()
        self._mandatory_payload_keys.add("nxosVersion")
        self._mandatory_payload_keys.add("policyName")
        self._mandatory_payload_keys.add("policyType")

        self._build_properties()

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # self.properties is already set in the parent class
        self.properties["payloads"] = None

    def _verify_payload(self, payload):
        """
        Verify that the payload is a dict and contains all mandatory keys
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dict. "
            msg += f"Got type {type(payload).__name__}, "
            msg += f"value {payload}"
            self.ansible_module.fail_json(msg, **self.failed_result)

        missing_keys = []
        for key in self._mandatory_payload_keys:
            if key not in payload:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += "payload is missing mandatory keys: "
        msg += f"{sorted(missing_keys)}"
        self.ansible_module.fail_json(msg, **self.failed_result)

    @property
    def payloads(self):
        """
        return the policy payloads
        """
        return self.properties["payloads"]

    @payloads.setter
    def payloads(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        for item in value:
            self._verify_payload(item)
        self.properties["payloads"] = value

    def _build_payloads_to_commit(self):
        """
        Build the payloads to commit to the controller.
        Populates the list self._payloads_to_commit

        Caller: commit()
        """
        method_name = inspect.stack()[0][3]
        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            self.ansible_module.fail_json(msg)

        self._image_policies.refresh()

        msg = f"self.payloads: {json.dumps(self.payloads, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        # Populate a list of policies on the contoller that match our payloads
        controller_policies = []
        policy_names = []
        for payload in self.payloads:
            if payload.get("policyName", None) not in self._image_policies.all_policies:
                continue
            controller_policies.append(payload)
            policy_names.append(payload["policyName"])

        msg = f"controller_policies: {json.dumps(controller_policies, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # fail_json if the ref_count for any policy is not 0 (i.e. the policy is in use
        # and cannot be replaced)
        self._verify_image_policy_ref_count(self._image_policies, policy_names)

        # If we made it this far, the ref_counts for all policies are 0
        # Merge the default image policy with the user's payload to create a
        # complete playload and add it to self._payloads_to_commit
        self._payloads_to_commit = []
        for payload in controller_policies:
            merge = MergeDicts(self.ansible_module)
            merge.dict1 = copy.deepcopy(self._default_policy(payload["policyName"]))
            merge.dict2 = payload
            msg = f"merge.dict1: {json.dumps(merge.dict1, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            msg = f"merge.dict2: {json.dumps(merge.dict2, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            merge.commit()
            self._payloads_to_commit.append(copy.deepcopy(merge.dict_merged))
        msg = "self._payloads_to_commit: "
        msg += f"{json.dumps(self._payloads_to_commit, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _send_payloads(self):
        """
        Send the payloads in self._payloads_to_commit to the controller

        Populate the following lists:

        - self.response_ok  : Controller responses associated with success result
        - self.result_ok    : Results where success is True
        - self.diff_ok      : Payloads for which the request succeeded
        - self.response_nok : Controller responses associated with failed result
        - self.result_nok   : Results where success is False
        - self.diff_nok     : Payloads for which the request failed

        Caller: commit()
        """
        self.response_ok = []
        self.result_ok = []
        self.diff_ok = []
        self.response_nok = []
        self.result_nok = []
        self.diff_nok = []

        for payload in self._payloads_to_commit:
            if self.check_mode is False:
                self.response_current = dcnm_send(
                    self.ansible_module, self.verb, self.path, data=json.dumps(payload)
                )
                self.result_current = self._handle_response(
                    self.response_current, self.verb
                )
            else:
                # check_mode is True so skip the request but update the diffs
                # and responses as if the request succeeded
                self.result_current = {"success": True}
                self.response_current = {"msg": "skipped: check_mode"}

            if self.result_current["success"]:
                self.response_ok.append(copy.deepcopy(self.response_current))
                self.result_ok.append(copy.deepcopy(self.result_current))
                self.diff_ok.append(copy.deepcopy(payload))
            else:
                self.response_nok.append(copy.deepcopy(self.response_current))
                self.result_nok.append(copy.deepcopy(self.result_current))
                self.diff_nok.append(copy.deepcopy(payload))

    def _process_responses(self):
        """
        Process the responses from the controller.
        Sets the following properties:
        - self.changed
        - self.diff
        - self.response
        - self.result
        - self.response_current
        - self.result_current

        Caller: commit()
        """
        method_name = inspect.stack()[0][3]
        if len(self.result_ok) == len(self._payloads_to_commit):
            self.changed = True
            self.failed = False
            for payload in self.diff_ok:
                payload["action"] = self.action
                self.diff = copy.deepcopy(payload)
            for response in self.response_ok:
                self.response = copy.deepcopy(response)
                self.response_current = copy.deepcopy(response)
            for result in self.result_ok:
                self.result = copy.deepcopy(result)
                self.result_current = copy.deepcopy(result)
            return

        self.failed = True
        self.changed = False
        if len(self.result_nok) != len(self._payloads_to_commit):
            self.changed = True
            for payload in self.diff_ok:
                payload["action"] = self.action
                self.diff = copy.deepcopy(payload)
            for response in self.response_ok:
                self.response = copy.deepcopy(response)
                self.response_current = copy.deepcopy(response)
            for result in self.result_ok:
                self.result = copy.deepcopy(result)
                self.result_current = copy.deepcopy(result)

        result = {}
        result["changed"] = self.changed
        result["diff"] = self.diff
        result["response"] = self.response
        result["result"] = self.result
        msg = f"{self.class_name}.{method_name}: "
        msg += "Bad response(s) during image policy bulk replace. "
        msg += f"response(s): {self.response_nok}"
        self.ansible_module.fail_json(msg, **result)

    def commit(self):
        """
        Commit the payloads to the controller
        """
        self._build_payloads_to_commit()
        self._send_payloads()
        self._process_responses()
