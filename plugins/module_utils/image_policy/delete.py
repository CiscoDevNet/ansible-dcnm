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


class ImagePolicyDelete(ImagePolicyCommon):
    """
    Delete image policies

    Usage:

    delete = ImagePolicyDelete(ansible_module)
    delete.policy_names = ["IMAGE_POLICY_1", "IMAGE_POLICY_2"]
    delete.commit()
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
        # self.properties is already set in the parent class
        self.properties["policy_names"] = None

    @property
    def policy_names(self):
        """
        return the policy names
        """
        return self.properties["policy_names"]

    @policy_names.setter
    def policy_names(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        self.properties["policy_names"] = value

    def _get_policies_to_delete(self):
        """
        Retrieve policies from the controller and return the list of
        controller policies that are in our policy_names list.
        """
        self.image_policies = ImagePolicies(self.ansible_module)
        self.image_policies.refresh()

        policies_to_delete = []
        for policy_name in self.policy_names:
            if policy_name in self.image_policies.all_policies:
                policies_to_delete.append(policy_name)
        return policies_to_delete

    def commit(self):
        """
        delete each of the image policies in self.policy_names

        1. TODO: If policy has ref_count > 0, detach policy from switches first
        2. Delete the policy
        """
        method_name = inspect.stack()[0][3]
        if self.policy_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.failed_result)

        path = self.endpoints.policy_delete["path"]
        verb = self.endpoints.policy_delete["verb"]

        policies_to_delete = self._get_policies_to_delete()

        if len(policies_to_delete) == 0:
            self.changed = False
            return

        policy_names = policies_to_delete
        self.log.log_msg(f"Deleting policies {policy_names}")
        request_body = {"policyNames": policy_names}

        response = dcnm_send(
            self.ansible_module, verb, path, data=json.dumps(request_body)
        )
        result = self._handle_response(response, verb)

        self.log.log_msg(f"response: {response}")

        if result["success"]:
            self.changed = True
            self.diff = request_body
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += "Bad response during policies delete. "
        msg += f"policy_names {policies_to_delete}. "
        msg += f"response: {response}"
        self.ansible_module.fail_json(msg)
