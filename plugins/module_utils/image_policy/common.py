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

import inspect
import logging
from typing import Any, Dict


class ImagePolicyCommon:
    """
    Common methods used by the other classes supporting
    dcnm_image_policy module

    Usage (where ansible_module is an instance of
    AnsibleModule or MockAnsibleModule):

    class MyClass(ImagePolicyCommon):
        def __init__(self, module):
            super().__init__(module)
        ...
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImagePolicyCommon()")

        self.ansible_module = ansible_module
        self.check_mode = self.ansible_module.check_mode
        self.state = ansible_module.params["state"]

        self.params = ansible_module.params

        self.properties: Dict[str, Any] = {}
        self.properties["results"] = None

    def _verify_image_policy_ref_count(self, instance, policy_names):
        """
        instance: ImagePolicies() instance
        policy_names: list of policy names

        Verify that all image policies in policy_names have a
        ref_count of 0 (i.e. no devices are using the policy).

        If the ref_count is greater than 0, fail_json with a message
        indicating that the policy, or policies, must be detached from
        all devices before it/they can be deleted.
        """
        method_name = inspect.stack()[0][3]
        _non_zero_ref_counts = {}
        for policy_name in policy_names:
            instance.policy_name = policy_name
            msg = f"instance.policy_name: {instance.policy_name}, "
            msg += f"instance.ref_count: {instance.ref_count}."
            self.log.debug(msg)
            # If the policy does not exist on the controller, the ref_count
            # will be None. We skip these too.
            if instance.ref_count in [0, None]:
                continue
            _non_zero_ref_counts[policy_name] = instance.ref_count
        if len(_non_zero_ref_counts) == 0:
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += "One or more policies have devices attached. "
        msg += "Detach these policies from all devices first using "
        msg += "the dcnm_image_upgrade module, with state == deleted. "
        for policy_name, ref_count in _non_zero_ref_counts.items():
            msg += f"policy_name: {policy_name}, "
            msg += f"ref_count: {ref_count}. "
        self.ansible_module.fail_json(msg, **self.results.failed_result)

    def _default_policy(self, policy_name):
        """
        Return a default policy payload for policy name.
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(policy_name, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_name must be a string. "
            msg += f"Got type {type(policy_name).__name__} for "
            msg += f"value {policy_name}."
            self.log.debug(msg)
            self.ansible_module.fail_json(msg, **self.results.failed_result)

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

    def _handle_response(self, response, verb):
        """
        Call the appropriate handler for response based on verb
        """
        if verb == "GET":
            return self._handle_get_response(response)
        if verb in {"POST", "PUT", "DELETE"}:
            return self._handle_post_put_delete_response(response)
        return self._handle_unknown_request_verbs(response, verb)

    def _handle_unknown_request_verbs(self, response, verb):
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Unknown request verb ({verb}) for response {response}."
        self.ansible_module.fail_json(msg)

    def _handle_get_response(self, response):
        """
        Caller:
            - self._handle_response()
        Handle controller responses to GET requests
        Returns: dict() with the following keys:
        - found:
            - False, if request error was "Not found" and RETURN_CODE == 404
            - True otherwise
        - success:
            - False if RETURN_CODE != 200 or MESSAGE != "OK"
            - True otherwise
        """
        result = {}
        success_return_codes = {200, 404}
        if (
            response.get("RETURN_CODE") == 404
            and response.get("MESSAGE") == "Not Found"
        ):
            result["found"] = False
            result["success"] = True
            return result
        if (
            response.get("RETURN_CODE") not in success_return_codes
            or response.get("MESSAGE") != "OK"
        ):
            result["found"] = False
            result["success"] = False
            return result
        result["found"] = True
        result["success"] = True
        return result

    def _handle_post_put_delete_response(self, response):
        """
        Caller:
            - self.self._handle_response()

        Handle POST, PUT, DELETE responses from the controller.

        Returns: dict() with the following keys:
        - changed:
            - True if changes were made to by the controller
                - ERROR key is not present
                - MESSAGE == "OK"
            - False otherwise
        - success:
            - False if MESSAGE != "OK" or ERROR key is present
            - True otherwise
        """
        result = {}
        if response.get("ERROR") is not None:
            result["success"] = False
            result["changed"] = False
            return result
        if response.get("MESSAGE") != "OK" and response.get("MESSAGE") is not None:
            result["success"] = False
            result["changed"] = False
            return result
        result["success"] = True
        result["changed"] = True
        return result

    def make_boolean(self, value):
        """
        Return value converted to boolean, if possible.
        Return value, if value cannot be converted.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ["true", "yes"]:
                return True
            if value.lower() in ["false", "no"]:
                return False
        return value

    def make_none(self, value):
        """
        Return None if value is an empty string, or a string
        representation of a None type
        Return value otherwise
        """
        if value in ["", "none", "None", "NONE", "null", "Null", "NULL"]:
            return None
        return value

    @property
    def results(self):
        """
        An instance of the Results class.
        """
        return self.properties["results"]

    @results.setter
    def results(self, value):
        self.properties["results"] = value
