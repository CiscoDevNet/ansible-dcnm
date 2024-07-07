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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.policymgnt.policymgnt import \
    EpPolicyAttach
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber


@Properties.add_rest_send
@Properties.add_results
@Properties.add_params
class ImagePolicyAttach():
    """
    ### Summary
    Attach image policies to one or more switches.

    ### Raises
    -   ValueError: if:
            -   ``policy_name`` is not set before calling commit.
            -   ``serial_numbers`` is not set before calling commit.
            -   ``serial_numbers`` is an empty list.
            -   ``policy_name`` does not exist on the controller.
            -   ``policy_name`` does not support the switch platform.
    -   TypeError: if:
            -   ``serial_numbers`` is not a list.

    ### Usage (where params is a dict with the following key/values:

    ```python
    params = {
        "check_mode": False,
        "state": "merged"
    }

    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = ImagePolicyAttach()
    instance.params = params
    instance.rest_send = rest_send
    instance.results = results
    instance.policy_name = "NR3F"
    instance.serial_numbers = ["FDO211218GC", "FDO211218HH"]
    instance.commit()
    ```

    ### Endpoint
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/attach-policy
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]


        self.endpoint = EpPolicyAttach()
        self.image_policies = ImagePolicies()
        self.path = None
        self.payloads = []
        self.switch_issu_details = SwitchIssuDetailsBySerialNumber()
        self.verb = None

        self._params = None
        self._rest_send = None
        self._results = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

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

        self.switch_issu_details.rest_send = self.rest_send
        self.switch_issu_details.results = self.results
        self.switch_issu_details.refresh()
        for serial_number in self.serial_numbers:
            self.switch_issu_details.filter = serial_number
            payload: dict = {}
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
                    self.ansible_module.fail_json(msg, **self.failed_result)
            self.payloads.append(payload)

    def verify_commit_parameters(self):
        """
        ### Summary
        Validations prior to commit() should be added here.

        ### Raises
        -   ValueError: if:
                -   ``policy_name`` is not set.
                -   ``serial_numbers`` is not set.
                -   ``policy_name`` does not exist on the controller.
                -   ``policy_name`` does not support the switch platform.
        """
        method_name = inspect.stack()[0][3]

        msg = "ENTERED"
        self.log.debug(msg)

        if self.policy_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.policy_name must be set before "
            msg += "calling commit()"
            raise ValueError(msg)

        if self.action == "query":
            return

        if self.serial_numbers is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.serial_numbers must be set before "
            msg += "calling commit()"
            raise ValueError(msg)

        self.image_policies.results = self.results
        self.image_policies.rest_send = self.rest_send  # pylint: disable=no-member

        self.image_policies.refresh()
        self.switch_issu_details.refresh()

        self.image_policies.policy_name = self.policy_name
        # Fail if the image policy does not exist.
        # Image policy creation is handled by a different module.
        if self.image_policies.name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"policy {self.policy_name} does not exist on "
            msg += "the controller."
            raise ValueError(msg)

        for serial_number in self.serial_numbers:
            self.switch_issu_details.filter = serial_number
            # Fail if the image policy does not support the switch platform
            if self.switch_issu_details.platform not in self.image_policies.platform:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"policy {self.policy_name} does not support platform "
                msg += f"{self.switch_issu_details.platform}. {self.policy_name} "
                msg += "supports the following platform(s): "
                msg += f"{self.image_policies.platform}"
                raise ValueError(msg)

    def commit(self):
        """
        ### Summary
        Attach image policy to switches.

        ### Raises
        -   ValueError: if:
                -   ``policy_name`` is not set.
                -   ``serial_numbers`` is not set.
                -   ``policy_name`` does not exist on the controller.
                -   ``policy_name`` does not support the switch platform.
        """
        method_name = inspect.stack()[0][3]

        msg = "ENTERED"
        self.log.debug(msg)

        try:
            self.verify_commit_parameters()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += r"Error while verifying commit parameters. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self._attach_policy()

    def _attach_policy(self):
        if self.check_mode is True:
            self._attach_policy_check_mode()
        else:
            self._attach_policy_normal_mode()

    def _attach_policy_check_mode(self):
        """
        Simulate _attach_policy()
        """
        self.build_payload()

        self.path = self.endpoints.policy_attach.get("path")
        self.verb = self.endpoints.policy_attach.get("verb")

        payload: dict = {}
        payload["mappingList"] = self.payloads

        self.response_current = {}
        self.response_current["RETURN_CODE"] = 200
        self.response_current["METHOD"] = self.verb
        self.response_current["REQUEST_PATH"] = self.path
        self.response_current["MESSAGE"] = "OK"
        self.response_current["DATA"] = "[simulated-check-mode-response:Success] "
        self.result_current = self._handle_response(self.response_current, self.verb)

        for payload in self.payloads:
            diff: dict = {}
            diff["action"] = self.action
            diff["ip_address"] = payload["ipAddr"]
            diff["logical_name"] = payload["hostName"]
            diff["policy_name"] = payload["policyName"]
            diff["serial_number"] = payload["serialNumber"]
            self.diff = copy.deepcopy(diff)

    def _attach_policy_normal_mode(self):
        """
        Attach policy_name to the switch(es) associated with serial_numbers

        This method creates a list of diffs, one result, and one response.
        These are accessable via:
            self.diff : list of dict
            self.result : result from the controller
            self.response : response from the controller
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.build_payload()

        self.path = self.endpoint.path
        self.verb = self.endpoint.verb

        payload: dict = {}
        payload["mappingList"] = self.payloads
        self.dcnm_send_with_retry(self.verb, self.path, payload)

        msg = f"result_current: {json.dumps(self.result_current, indent=4)}"
        self.log.debug(msg)
        msg = f"response_current: {json.dumps(self.response_current, indent=4)}"
        self.log.debug(msg)

        if not self.result_current["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Bad result when attaching policy {self.policy_name} "
            msg += f"to switch. Payload: {payload}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        for payload in self.payloads:
            diff: dict = {}
            diff["action"] = self.action
            diff["ip_address"] = payload["ipAddr"]
            diff["logical_name"] = payload["hostName"]
            diff["policy_name"] = payload["policyName"]
            diff["serial_number"] = payload["serialNumber"]
            self.diff = copy.deepcopy(diff)

    @property
    def policy_name(self):
        """
        Set the name of the policy to attach, detach, query.

        Must be set prior to calling instance.commit()
        """
        return self._policy_name

    @policy_name.setter
    def policy_name(self, value):
        self._policy_name = value

    @property
    def serial_numbers(self):
        """
        ### Summary
        Set the serial numbers of the switches to/ which
        policy_name will be attached.

        Must be set prior to calling commit()

        ### Raises
        - TypeError: if value is not a list.
        - ValueError: if value is an empty list.
        """
        return self._serial_numbers

    @serial_numbers.setter
    def serial_numbers(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.serial_numbers must be a "
            msg += "python list of switch serial numbers. "
            msg += f"Got {value}."
            raise TypeError(msg, **self.failed_result)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.serial_numbers must contain at least one "
            msg += "switch serial number."
            raise ValueError(msg, **self.failed_result)
        self._serial_numbers = value
