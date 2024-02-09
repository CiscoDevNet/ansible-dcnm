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
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints


class ImagePolicyQuery(ImagePolicyCommon):
    """
    Query image policies

    Usage:

    instance = ImagePolicyQuery(ansible_module)
    instance.policy_names = ["IMAGE_POLICY_1", "IMAGE_POLICY_2"]
    instance.commit()
    diff = instance.diff # contains the image policy information
    result = instance.result # contains the result(s) of the query
    response = instance.response # contains the response(s) from the controller
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED ImagePolicyQuery()"
        self.log.debug(msg)

        self._build_properties()
        self.endpoints = ApiEndpoints()
        self.image_policies = ImagePolicies(self.ansible_module)

        self.action = "query"
        self.changed = False

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

    def _get_policies_to_query(self):
        """
        Retrieve policies from the controller and return the list of
        controller policies that are in our policy_names list.
        """
        self.image_policies.refresh()

        policies_to_query = []
        for policy_name in self.policy_names:
            if policy_name in self.image_policies.all_policies:
                policies_to_query.append(policy_name)
        return policies_to_query

    def commit(self):
        """
        query each of the image policies in self.policy_names
        """
        method_name = inspect.stack()[0][3]
        if self.policy_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.failed_result)

        policies_to_query = self._get_policies_to_query()

        if len(policies_to_query) == 0:
            return

        msg = f"Querying policies {policies_to_query}"
        self.log.debug(msg)

        instance = ImagePolicies(self.ansible_module)
        instance.refresh()

        for policy_name in policies_to_query:
            if policy_name in instance.all_policies:
                policy = copy.deepcopy(instance.all_policies[policy_name])
                policy["action"] = self.action
                self.diff = policy
        self.response = copy.deepcopy(instance.response)
        self.response_current = copy.deepcopy(instance.response)
        self.result = copy.deepcopy(instance.result)
        self.result_current = copy.deepcopy(instance.result_current)
