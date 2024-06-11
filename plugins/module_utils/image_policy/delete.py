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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results


class ImagePolicyDelete(ImagePolicyCommon):
    """
    Delete image policies

    Usage:

    instance = ImagePolicyDelete(ansible_module)
    instance.policy_names = ["IMAGE_POLICY_1", "IMAGE_POLICY_2"]
    instance.commit()
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__
        self.action = "delete"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._policies_to_delete = []
        self._build_properties()
        self.endpoints = ApiEndpoints()
        self._image_policies = ImagePolicies(self.ansible_module)
        self._image_policies.results = Results()
        self.rest_send = RestSend(self.ansible_module)

        self.path = self.endpoints.policy_delete["path"]
        self.verb = self.endpoints.policy_delete["verb"]

        msg = "ENTERED ImagePolicyDelete(): "
        msg += f"action: {self.action}, "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # self.properties is already set in the parent class
        self.properties["policy_names"] = None

    def _get_policies_to_delete(self) -> None:
        """
        Retrieve policies from the controller and return the list of
        controller policies that are in our policy_names list.
        """
        self._image_policies.refresh()
        self._verify_image_policy_ref_count(self._image_policies, self.policy_names)

        self._policies_to_delete = []
        for policy_name in self.policy_names:
            if policy_name in self._image_policies.all_policies:
                msg = f"Policy {policy_name} exists on the controller. "
                msg += f"Appending {policy_name} to _policies_to_delete."
                self.log.debug(msg)
                self._policies_to_delete.append(policy_name)

    def _validate_commit_parameters(self):
        """
        validate the parameters for commit
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if self.policy_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

    def commit(self):
        """
        delete each of the image policies in self.policy_names
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self._validate_commit_parameters()

        self._get_policies_to_delete()

        msg = f"self._policies_to_delete: {self._policies_to_delete}"
        self.log.debug(msg)
        if len(self._policies_to_delete) != 0:
            self._send_requests()
        else:
            self.results.action = self.action
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.diff_current = {}
            self.results.result_current = {"success": True, "changed": False}
            msg = "No image policies to delete"
            self.results.changed = False
            self.results.failed = False
            self.results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
            self.log.debug(msg)

    def _send_requests(self):
        """
        If check_mode is False, send the requests to the controller
        If check_mode is True, do not send the requests to the controller

        In both cases, populate the following lists:

        - self.response_ok  : list of controller responses associated with success result
        - self.result_ok    : list of results where success is True
        - self.diff_ok      : list of payloads for which the request succeeded
        - self.response_nok : list of controller responses associated with failed result
        - self.result_nok   : list of results where success is False
        - self.diff_nok     : list of payloads for which the request failed
        """
        self.rest_send.check_mode = self.check_mode

        # We don't want RestSend to retry on errors since the likelihood of a
        # timeout error when deleting image policies is low, and there
        # are cases of permanent errors for which we don't want to retry.
        self.rest_send.timeout = 1

        msg = f"Deleting policies {self._policies_to_delete}"
        self.log.debug(msg)

        self.payload = {"policyNames": self._policies_to_delete}
        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.payload = copy.deepcopy(self.payload)
        self.rest_send.commit()

        self.register_result()

    def register_result(self):
        """
        Register the result of the fabric create request
        """
        msg = f"self.rest_send.result_current: {self.rest_send.result_current}"
        self.log.debug(msg)
        if self.rest_send.result_current["success"]:
            self.results.failed = False
            self.results.diff_current = self.payload
        else:
            self.results.diff_current = {}
            self.results.failed = True

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state
        self.results.result_current = self.rest_send.result_current
        self.results.response_current = self.rest_send.response_current
        self.results.register_task_result()

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
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "policy_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                self.ansible_module.fail_json(msg)
        self.properties["policy_names"] = value
