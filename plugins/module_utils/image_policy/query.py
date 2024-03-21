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

from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results


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

        self._policies_to_query = []
        self._build_properties()
        self._image_policies = ImagePolicies(self.ansible_module)
        self._image_policies.results = Results()

        self.action = "query"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED ImagePolicyQuery(): "
        msg += f"action {self.action}, "
        msg += f"check_mode {self.check_mode}, "
        msg += f"state {self.state}"
        self.log.debug(msg)

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
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be a list of at least one string. "
            msg += f"got {value}."
            self.ansible_module.fail_json(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "policy_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                self.ansible_module.fail_json(msg)
        self.properties["policy_names"] = value

    def commit(self):
        """
        query each of the image policies in self.policy_names
        """
        method_name = inspect.stack()[0][3]
        if self.policy_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        self._image_policies.refresh()

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state

        if self._image_policies.results.result_current.get("success") is False:
            self.results.diff_current = {}
            self.results.failed = True
            self.results.response_current = copy.deepcopy(self._image_policies.results.response_current)
            self.results.result_current = copy.deepcopy(self._image_policies.results.result_current)
            self.results.register_task_result()
            return

        self.results.failed = False
        registered_a_result = False
        for policy_name in self.policy_names:
            if policy_name not in self._image_policies.all_policies:
                continue
            self.results.diff_current = copy.deepcopy(self._image_policies.all_policies[policy_name])
            self.results.response_current = copy.deepcopy(self._image_policies.results.response_current)
            self.results.result_current = copy.deepcopy(self._image_policies.results.result_current)
            self.results.register_task_result()
            registered_a_result = True

        if registered_a_result is False:
            self.results.failed = False
            self.results.diff_current = {}
            # Avoid a failed result if none of the policies were found
            self.results.result_current = {"success": True}
            self.results.register_task_result()
