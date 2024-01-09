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

import inspect
import json
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class ImagePolicyAction(ImageUpgradeCommon):
    """
    Perform image policy actions on the controller for one or more switches.

    Support for the following actions:
        - attach
        - detach
        - query

    Usage (where module is an instance of AnsibleModule):

    instance = ImagePolicyAction(module)
    instance.policy_name = "NR3F"
    instance.action = "attach" # or detach, or query
    instance.serial_numbers = ["FDO211218GC", "FDO211218HH"]
    instance.commit()
    # for query only
    query_result = instance.query_result

    Endpoints:
    For action == attach:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/attach-policy
    For action == detach:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy
    For action == query:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/image-policy/__POLICY_NAME__
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImagePolicyAction()")

        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.endpoints = ApiEndpoints()
        self._init_properties()
        self.image_policies = ImagePolicies(self.module)
        self.path = None
        self.payloads = []
        self.switch_issu_details = SwitchIssuDetailsBySerialNumber(self.module)
        self.valid_actions = {"attach", "detach", "query"}
        self.verb = None

    def _init_properties(self):
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        # self.properties is already initialized in the parent class
        self.properties["action"] = None
        self.properties["response"] = None
        self.properties["result"] = None
        self.properties["policy_name"] = None
        self.properties["query_result"] = None
        self.properties["serial_numbers"] = None

    def build_payload(self):
        """
        build the payload to send in the POST request
        to attach policies to devices

        caller _attach_policy()
        """
        method_name = inspect.stack()[0][3]
        self.payloads = []

        self.switch_issu_details.refresh()
        for serial_number in self.serial_numbers:
            self.switch_issu_details.filter = serial_number
            payload = {}
            payload["policyName"] = self.policy_name
            payload["hostName"] = self.switch_issu_details.device_name
            payload["ipAddr"] = self.switch_issu_details.ip_address
            payload["platform"] = self.switch_issu_details.platform
            payload["serialNumber"] = self.switch_issu_details.serial_number
            for key, value in payload.items():
                if value is None:
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f" Unable to determine {key} for switch "
                    msg += f"{self.switch_issu_details.ip_address}, "
                    msg += f"{self.switch_issu_details.serial_number}, "
                    msg += f"{self.switch_issu_details.device_name}. "
                    msg += "Please verify that the switch is managed by "
                    msg += "the controller."
                    self.module.fail_json(msg, **self.failed_result)
            self.payloads.append(payload)

    def validate_request(self):
        """
        validations prior to commit() should be added here.
        """
        method_name = inspect.stack()[0][3]

        if self.action is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.action must be set before "
            msg += "calling commit()"
            self.module.fail_json(msg, **self.failed_result)

        if self.policy_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.policy_name must be set before "
            msg += "calling commit()"
            self.module.fail_json(msg, **self.failed_result)

        if self.action == "query":
            return

        if self.serial_numbers is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.serial_numbers must be set before "
            msg += "calling commit()"
            self.module.fail_json(msg, **self.failed_result)

        self.image_policies.refresh()
        self.switch_issu_details.refresh()

        # Fail if the image policy does not support the switch platform
        self.image_policies.policy_name = self.policy_name
        for serial_number in self.serial_numbers:
            self.switch_issu_details.filter = serial_number
            if self.switch_issu_details.platform not in self.image_policies.platform:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"policy {self.policy_name} does not support platform "
                msg += f"{self.switch_issu_details.platform}. {self.policy_name} "
                msg += "supports the following platform(s): "
                msg += f"{self.image_policies.platform}"
                self.module.fail_json(msg, **self.failed_result)

    def commit(self):
        """
        Call one of the following methods to commit the action to the controller:
        - _attach_policy
        - _detach_policy
        - _query_policy
        """
        method_name = inspect.stack()[0][3]

        self.validate_request()
        if self.action == "attach":
            self._attach_policy()
        elif self.action == "detach":
            self._detach_policy()
        elif self.action == "query":
            self._query_policy()
        else:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Unknown action {self.action}."
            self.module.fail_json(msg, **self.failed_result)

    def _attach_policy(self):
        """
        Attach policy_name to the switch(es) associated with serial_numbers

        NOTES:
        1. This method creates a list of responses and results which
        are accessible via properties response and result,
        respectively.
        """
        method_name = inspect.stack()[0][3]

        self.build_payload()

        self.path = self.endpoints.policy_attach.get("path")
        self.verb = self.endpoints.policy_attach.get("verb")

        responses = []
        results = []

        for payload in self.payloads:
            response = dcnm_send(
                self.module, self.verb, self.path, data=json.dumps(payload)
            )
            result = self._handle_response(response, self.verb)

            msg = f"{self.class_name}.{method_name}: "
            msg += f"response: {json.dumps(response, indent=4)}"
            self.log.debug(msg)

            if not result["success"]:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Bad result when attaching policy {self.policy_name} "
                msg += f"to switch {payload['ipAddr']}."
                self.module.fail_json(msg, **self.failed_result)

            responses.append(response)
            results.append(result)

        self.properties["response"] = responses
        self.properties["result"] = results

    def _detach_policy(self):
        """
        Detach policy_name from the switch(es) associated with serial_numbers
        verb: DELETE
        endpoint: /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy
        query_params: ?serialNumber=FDO211218GC,FDO21120U5D
        """
        method_name = inspect.stack()[0][3]

        self.path = self.endpoints.policy_detach.get("path")
        self.verb = self.endpoints.policy_detach.get("verb")

        query_params = ",".join(self.serial_numbers)
        self.path += f"?serialNumber={query_params}"

        self.properties["response"] = dcnm_send(self.module, self.verb, self.path)
        self.properties["result"] = self._handle_response(self.response, self.verb)

        if not self.result["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Bad result when detaching policy {self.policy_name} "
            msg += f"from the following device(s):  {','.join(sorted(self.serial_numbers))}."
            self.module.fail_json(msg, **self.failed_result)

        self.changed = True
        self.diff = self.response

    def _query_policy(self):
        """
        Query the image policy
        verb: GET
        endpoint: /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/image-policy
        """
        method_name = inspect.stack()[0][3]

        self.path = self.endpoints.policy_info.get("path")
        self.verb = self.endpoints.policy_info.get("verb")

        self.path = self.path.replace("__POLICY_NAME__", self.policy_name)

        self.properties["response"] = dcnm_send(self.module, self.verb, self.path)
        self.properties["result"] = self._handle_response(self.response, self.verb)

        if not self.result["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Bad result when querying image policy {self.policy_name}."
            self.module.fail_json(msg, **self.failed_result)

        self.properties["query_result"] = self.response.get("DATA")

    @property
    def query_result(self):
        """
        Return the value of properties["query_result"].
        """
        return self.properties.get("query_result")

    @property
    def action(self):
        """
        Set the action to take.

        One of "attach", "detach", "query"

        Must be set prior to calling instance.commit()
        """
        return self.properties.get("action")

    @action.setter
    def action(self, value):
        method_name = inspect.stack()[0][3]

        if value not in self.valid_actions:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.action must be one of "
            msg += f"{','.join(sorted(self.valid_actions))}. "
            msg += f"Got {value}."
            self.module.fail_json(msg, **self.failed_result)

        self.properties["action"] = value

    @property
    def response(self):
        """
        Return the raw response from the controller.

        Assumes that commit() has been called.

        In the case of attach, this is a list of responses.
        """
        return self.properties.get("response")

    @property
    def result(self):
        """
        Return the raw result.

        Assumes that commit() has been called.

        In the case of attach, this is a list of results.
        """
        return self.properties.get("result")

    @property
    def policy_name(self):
        """
        Set the name of the policy to attach, detach, query.

        Must be set prior to calling instance.commit()
        """
        return self.properties.get("policy_name")

    @policy_name.setter
    def policy_name(self, value):
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.properties["policy_name"] = value

    @property
    def serial_numbers(self):
        """
        Set the serial numbers of the switches to/from which
        policy_name will be attached or detached.

        Must be set prior to calling instance.commit()
        """
        return self.properties.get("serial_numbers")

    @serial_numbers.setter
    def serial_numbers(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.serial_numbers must be a "
            msg += "python list of switch serial numbers. "
            msg += f"Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["serial_numbers"] = value
