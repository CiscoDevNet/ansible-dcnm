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
from typing import Any, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class PolicyCreateBulk(ImagePolicyCommon):
    """
    Given a list of payloads, bulk-create the image policies therein.
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self._build_properties()
        self.endpoints = ApiEndpoints()

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # properties is already initialized in the parent class
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
                msg += f"got a list, but one of the items is "
                msg += f"type {type(item).__name__}, "
                msg += f"value {item}"
                self.ansible_module.fail_json(msg)
        self.properties["payloads"] = value

    def commit(self):
        """
        create policies.  Skip any policies that already exist
        on the controller,
        """
        method_name = inspect.stack()[0][3]
        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            self.ansible_module.fail_json(msg)

        self.image_policies = ImagePolicies(self.ansible_module)
        self.image_policies.refresh()

        path = self.endpoints.policy_create["path"]
        verb = self.endpoints.policy_create["verb"]

        payloads_to_commit = []
        for payload in self.payloads:
            if payload.get("policyName", None) in self.image_policies.all_policies:
                continue
            payloads_to_commit.append(payload)

        if len(payloads_to_commit) == 0:
            self.changed = False
            msg = f"{self.class_name}.{method_name}: "
            msg += "No policies to create."
            self.log.log_msg(msg)
            return

        result_ok = []
        diff_ok = []
        result_nok = []
        diff_nok = []
        for payload in payloads_to_commit:
            response = dcnm_send(
                self.ansible_module, verb, path, data=json.dumps(payload)
            )
            result = self._handle_response(response, verb)

            if result["success"]:
                result_ok.append(response)
                diff_ok.append(payload)
            else:
                result_nok.append(response)
                diff_nok.append(payload)

        if len(result_ok) == len(payloads_to_commit):
            self.changed = True
            for diff in diff_ok:
                self.diff = diff
            return

        self.changed = False
        # at least one request succeeded, so set changed to True
        if len(result_nok) != len(payloads_to_commit):
            self.changed = True

        result = {}
        result["changed"] = self.changed
        result["diff"] = diff_ok
        msg = f"{self.class_name}.{method_name}: "
        msg += "Bad response(s) during policy create. "
        msg += f"policy_name {self.policy_name}. "
        msg += f"response(s): {result_nok}"
        self.ansible_module.fail_json(msg, **result)


class PolicyCreate(ImagePolicyCommon):
    """
    Given a properly-constructed image policy payload (python dict),
    send an image policy create request to the controller.  The payload
    format is given below.

    agnostic        bool(), optional. true or false
    epldImgName     str(), optional. name of an EPLD image to install.
    nxosVersion     str(), required. NX-OS version as version_type_arch
    packageName:    str(), optional, A comma-separated list of packages
    platform:       str(), optional, one of N9K, N6K, N5K, N3K
    policyDesc      str(), optional, description for the image policy
    policyName:     str(), required.  Name of the image policy.
    policyType      str(), required. PLATFORM or UMBRELLA
    rpmimages:      str(), optional. A comma-separated list of packages to uninstall

    Example:

    {
        "agnostic": false,
        "epldImgName": "n9000-epld.10.3.2.F.img",
        "nxosVersion": "10.3.1_nxos64-cs_64bit",
        "packageName": "mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm",
        "platform": "N9K",
        "policyDescr": "image policy of 10.3(3)F",
        "policyName": "FOO",
        "policyType": "PLATFORM",
        "rpmimages": "mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000"
    }

    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self._mandatory_keys = set()
        self._mandatory_keys.add("nxosVersion")
        self._mandatory_keys.add("policyName")
        self._mandatory_keys.add("policyType")

        self._build_properties()
        self.endpoints = ApiEndpoints()

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # properties is already initialized in the parent class
        self.properties["payload"] = None

    def _verify_payload(self, payload):
        method_name = inspect.stack()[0][3]
        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dict. "
            msg += f"gpt type {type(payload).__name__}, "
            msg += f"value {payload}"
            self.ansible_module.fail_json(msg, **self.failed_result)
        missing_keys = []
        for key in self._mandatory_keys:
            if key not in payload:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += f"payload is missing mandatory keys: "
        msg += f"{sorted(missing_keys)}"
        self.ansible_module.fail_json(msg, **self.failed_result)

    @property
    def payload(self):
        """
        This class expects a properly-defined image policy payload.
        See class docstring for the payload structure.
        """
        return self.properties["payload"]

    @payload.setter
    def payload(self, value):
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self._verify_payload(value)
        self.properties["payload"] = value

    def commit(self):
        """
        create policy.  If policy already exists
        on the controller, do nothing.
        """
        method_name = inspect.stack()[0][3]
        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.failed_result)

        path = self.endpoints.policy_create["path"]
        verb = self.endpoints.policy_create["verb"]

        self.image_policies = ImagePolicies(self.ansible_module)
        self.image_policies.refresh()

        if self.payload.get("policyName") in self.image_policies.all_policies:
            return

        response = dcnm_send(
            self.ansible_module, verb, path, data=json.dumps(self.payload)
        )
        result = self._handle_response(response, verb)

        if result["success"]:
            self.ansible_module.result["changed"] = True
            return

        self.ansible_module.result["changed"] = False
        msg = f"{self.class_name}.{method_name}: "
        msg += "Bad response during policy create. "
        msg += f"policy_name {self.policy_name}. "
        msg += f"response: {response}"
        self.ansible_module.fail_json(msg)
