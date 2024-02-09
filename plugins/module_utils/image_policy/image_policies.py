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
from typing import Any, AnyStr, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class ImagePolicies(ImagePolicyCommon):
    """
    Retrieve image policy details from the controller and provide
    property accessors for the policy attributes.

    Usage (where module is an instance of AnsibleModule):

    instance = ImagePolicies(module).refresh()
    instance.policy_name = "NR3F"
    if instance.name is None:
        print("policy NR3F does not exist on the controller")
        exit(1)
    policy_name = instance.name
    platform = instance.platform
    epd_image_name = instance.epld_image_name
    etc...

    Policies can be refreshed by calling instance.refresh().

    Endpoint:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImagePolicies()")

        self.method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.endpoints = ApiEndpoints()
        self._init_properties()

    def _init_properties(self):
        self.method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        # self.properties is already initialized in the parent class
        self.properties["all_policies"] = None
        self.properties["policy_name"] = None
        self.properties["response_data"] = {}
        self.properties["response"] = None
        self.properties["result"] = None

    def refresh(self):
        """
        Refresh self.image_policies with current image policies from the controller
        """
        self.method_name = inspect.stack()[0][3]

        path = self.endpoints.policies_info.get("path")
        verb = self.endpoints.policies_info.get("verb")

        self.properties["response"] = dcnm_send(self.ansible_module, verb, path)
        self.properties["result"] = self._handle_response(self.response, verb)

        if not self.result["success"]:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "Bad result when retrieving image policy "
            msg += "information from the controller."
            self.ansible_module.fail_json(msg, **self.failed_result)

        data = self.response.get("DATA").get("lastOperDataObject")

        if data is None:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "Bad response when retrieving image policy "
            msg += "information from the controller."
            self.ansible_module.fail_json(msg, **self.failed_result)

        # We cannot fail_json here since dcnm_image_policy merged
        # state will fail if there are no policies defined.
        # if len(data) == 0:
        #     msg = f"{self.class_name}.{self.method_name}: "
        #     msg += "the controller has no defined image policies."
        #     self.ansible_module.fail_json(msg, **self.failed_result)

        if len(data) == 0:
            msg = "the controller has no defined image policies."
            self.log.debug(msg)

        self.properties["response_data"] = {}
        self.properties["all_policies"] = {}
        for policy in data:
            policy_name = policy.get("policyName")

            if policy_name is None:
                msg = f"{self.class_name}.{self.method_name}: "
                msg += "Cannot parse policy information from the controller."
                self.ansible_module.fail_json(msg, **self.failed_result)

            self.properties["response_data"][policy_name] = policy

        self.properties["all_policies"] = copy.deepcopy(
            self.properties["response_data"]
        )

    def _get(self, item):
        self.method_name = inspect.stack()[0][3]

        if self.policy_name is None:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "instance.policy_name must be set before "
            msg += f"accessing property {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if self.policy_name not in self.properties["response_data"]:
            return None

        if item == "policy":
            return self.properties["response_data"][self.policy_name]

        if item not in self.properties["response_data"][self.policy_name]:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += f"{self.policy_name} does not have a key named {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        return self.make_boolean(
            self.make_none(self.properties["response_data"][self.policy_name][item])
        )

    @property
    def all_policies(self) -> Dict[AnyStr, Any]:
        """
        Return dict containing all policies, keyed on policy_name
        """
        if self.properties["all_policies"] is None:
            return {}
        return self.properties["all_policies"]

    @property
    def description(self):
        """
        Return the policyDescr of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("policyDescr")

    @property
    def epld_image_name(self):
        """
        Return the epldImgName of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("epldImgName")

    @property
    def name(self):
        """
        Return the name of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("policyName")

    @property
    def response_data(self):
        """
        Return the parsed data from the response as a dictionary,
        keyed on policy_name.
        """
        return self.properties["response_data"]

    @property
    def response(self):
        """
        Return the raw response from the controller.
        """
        return self.properties["response"]

    @property
    def result(self):
        """
        Return the raw result.
        """
        return self.properties["result"]

    @property
    def policy_name(self):
        """
        Set the name of the policy to query.

        This must be set prior to accessing any other properties
        """
        return self.properties.get("policy_name")

    @policy_name.setter
    def policy_name(self, value):
        self.properties["policy_name"] = value

    @property
    def policy(self):
        """
        Return the policy data of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("policy")

    @property
    def policy_type(self):
        """
        Return the policyType of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("policyType")

    @property
    def nxos_version(self):
        """
        Return the nxosVersion of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("nxosVersion")

    @property
    def package_name(self):
        """
        Return the packageName of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("packageName")

    @property
    def platform(self):
        """
        Return the platform of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("platform")

    @property
    def platform_policies(self):
        """
        Return the platformPolicies of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("platformPolicies")

    @property
    def ref_count(self):
        """
        Return the reference count of the policy matching self.policy_name,
        if it exists.  The reference count is the number of switches using
        this policy.
        Return None otherwise
        """
        return self._get("ref_count")

    @property
    def rpm_images(self):
        """
        Return the rpmimages of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("rpmimages")

    @property
    def image_name(self):
        """
        Return the imageName of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("imageName")

    @property
    def agnostic(self):
        """
        Return the value of agnostic for the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("agnostic")
