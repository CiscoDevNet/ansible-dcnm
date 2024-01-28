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
import json
import logging
from typing import Any, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber


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

        self.endpoints = ApiEndpoints()
        self._init_properties()
        self.image_policies = ImagePolicies(self.module)
        self.path = None
        self.payloads = []
        self.switch_issu_details = SwitchIssuDetailsBySerialNumber(self.module)
        self.valid_actions = {"attach", "detach", "query"}
        self.verb = None

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        self.properties["action"] = None
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

        msg = "ENTERED"
        self.log.debug(msg)

        self.payloads = []

        self.switch_issu_details.refresh()
        for serial_number in self.serial_numbers:
            self.switch_issu_details.filter = serial_number
            payload: Dict[str, Any] = {}
            payload["policyName"] = self.policy_name
            payload["hostName"] = self.switch_issu_details.device_name
            payload["ipAddr"] = self.switch_issu_details.ip_address
            payload["platform"] = self.switch_issu_details.platform
            payload["serialNumber"] = self.switch_issu_details.serial_number
            msg = f"payload: {json.dumps(payload, indent=4)}"
            self.log.debug(msg)
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

        msg = "ENTERED"
        self.log.debug(msg)

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

        self.image_policies.policy_name = self.policy_name
        # Fail if the image policy does not exist.
        # Image policy creation is handled by a different module.
        if self.image_policies.name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"policy {self.policy_name} does not exist on "
            msg += "the controller"
            self.module.fail_json(msg)

        for serial_number in self.serial_numbers:
            self.switch_issu_details.filter = serial_number
            # Fail if the image policy does not support the switch platform
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

        msg = "ENTERED"
        self.log.debug(msg)

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

        This method creates a list of diffs, one result, and one response.
        These are accessable via:
            self.diff = List[Dict[str, Any]]
            self.result = result from the controller
            self.response = response from the controller
        """
        method_name = inspect.stack()[0][3]

        msg = "ENTERED"
        self.log.debug(msg)

        self.build_payload()

        self.path = self.endpoints.policy_attach.get("path")
        self.verb = self.endpoints.policy_attach.get("verb")

        payload: Dict[str, Any] = {}
        payload["mappingList"] = self.payloads
        self.dcnm_send_with_retry(self.verb, self.path, payload)

        if not self.result_current["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Bad result when attaching policy {self.policy_name} "
            msg += f"to switch {payload['ipAddr']}."
            self.module.fail_json(msg, **self.failed_result)

        for payload in self.payloads:
            diff: Dict[str, Any] = {}
            diff["action"] = self.action
            diff["ip_address"] = payload["ipAddr"]
            diff["logical_name"] = payload["hostName"]
            diff["policy_name"] = payload["policyName"]
            diff["serial_number"] = payload["serialNumber"]
            self.diff = copy.deepcopy(diff)

    def _detach_policy(self):
        """
        Detach policy_name from the switch(es) associated with serial_numbers
        verb: DELETE
        endpoint: /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy
        query_params: ?serialNumber=FDO211218GC,FDO21120U5D
        """
        method_name = inspect.stack()[0][3]

        msg = "ENTERED"
        self.log.debug(msg)

        self.path = self.endpoints.policy_detach.get("path")
        self.verb = self.endpoints.policy_detach.get("verb")

        query_params = ",".join(self.serial_numbers)
        self.path += f"?serialNumber={query_params}"

        self.dcnm_send_with_retry(self.verb, self.path)

        if not self.result_current["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Bad result when detaching policy {self.policy_name} "
            msg += f"from the following device(s):  {','.join(sorted(self.serial_numbers))}."
            self.module.fail_json(msg, **self.failed_result)

        for serial_number in self.serial_numbers:
            self.switch_issu_details.filter = serial_number
            diff: Dict[str, Any] = {}
            diff["action"] = self.action
            diff["ip_address"] = self.switch_issu_details.ip_address
            diff["logical_name"] = self.switch_issu_details.device_name
            diff["policy_name"] = self.policy_name
            diff["serial_number"] = serial_number
            self.diff = copy.deepcopy(diff)
        self.changed = True

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

        self.dcnm_send_with_retry(self.verb, self.path)

        if not self.result_current["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Bad result when querying image policy {self.policy_name}."
            self.module.fail_json(msg, **self.failed_result)

        self.query_result = self.response_current.get("DATA")
        self.diff = self.response_current

    @property
    def diff_null(self):
        """
        Convenience property to return a null diff when no action is taken.
        """
        diff: Dict[str, Any] = {}
        diff["action"] = None
        diff["ip_address"] = None
        diff["logical_name"] = None
        diff["policy"] = None
        diff["serial_number"] = None
        return diff

    @property
    def query_result(self):
        """
        Return the value of properties["query_result"].
        """
        return self.properties.get("query_result")

    @query_result.setter
    def query_result(self, value):
        method_name = inspect.stack()[0][3]
        if isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.query_result must be a dict. "
            msg += f"Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["query_result"] = value

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
    def policy_name(self):
        """
        Set the name of the policy to attach, detach, query.

        Must be set prior to calling instance.commit()
        """
        return self.properties.get("policy_name")

    @policy_name.setter
    def policy_name(self, value):
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
