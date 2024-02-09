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
# TODO: needs_testing

from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
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

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED ImagePolicyReplaceBulk()"
        self.log.debug(msg)

        self.action = "replace"
        self.response_ok = []
        self.result_ok = []
        self.diff_ok = []
        self.response_nok = []
        self.result_nok = []
        self.diff_nok = []
        self._payloads_to_commit = []

        self._build_properties()
        self.endpoints = ApiEndpoints()
        self.image_policies = ImagePolicies(self.ansible_module)

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # self.properties is already set in the parent class
        self.properties["payloads"] = None

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
            if not isinstance(item, dict):
                msg = f"{self.class_name}.{method_name}: "
                msg += "payloads must be a list of dict. "
                msg += "got a list, but one of the items is "
                msg += f"type {type(item).__name__}, "
                msg += f"value {item}"
                self.ansible_module.fail_json(msg)
        self.properties["payloads"] = value

    def default_policy(self, policy_name):
        """
        Return a default policy payload for the given policy name.
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(policy_name, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_name must be a string. "
            msg += f"got {type(policy_name).__name__} for "
            msg += f"value {policy_name}"
            self.ansible_module.fail_json(msg)

        policy = {
            "agnostic": False,
            "epldImgName": "",
            "nxosVersion": "",
            "packageName": "",
            "platform": "",
            "policyDescr": "",
            "policyName": policy_name,
            "policyType": "PLATFORM",
            "rpmimages": "",
        }
        return policy

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

        self.image_policies.refresh()

        controller_policies = []
        for payload in self.payloads:
            if payload.get("policyName", None) not in self.image_policies.all_policies:
                continue
            controller_policies.append(payload)

        self._payloads_to_commit = []
        for payload in controller_policies:
            merge = MergeDicts(self.ansible_module)
            merge.dict1 = copy.deepcopy(self.default_policy(payload["policyName"]))
            merge.dict2 = payload
            merge.commit()
            self._payloads_to_commit.append(copy.deepcopy(merge.dict_merged))

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
        path = self.endpoints.policy_edit.get("path")
        verb = self.endpoints.policy_edit.get("verb")

        for payload in self._payloads_to_commit:
            response = dcnm_send(
                self.ansible_module, verb, path, data=json.dumps(payload)
            )
            result = self._handle_response(response, verb)

            if result["success"]:
                self.response_ok.append(response)
                self.result_ok.append(result)
                self.diff_ok.append(payload)
            else:
                self.response_nok.append(response)
                self.result_nok.append(response)
                self.diff_nok.append(payload)

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
