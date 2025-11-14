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

from ..common.api.v1.imagemanagement.rest.policymgnt.policymgnt import \
    EpPolicyAttach
from ..common.image_policies import ImagePolicies
from ..common.properties import Properties
from ..common.results import Results
from .switch_issu_details import SwitchIssuDetailsBySerialNumber
from .wait_for_controller_done import WaitForControllerDone


@Properties.add_rest_send
@Properties.add_results
class ImagePolicyAttach:
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

    ### Usage

    ```python
    # params is typically obtained from ansible_module.params
    # but can also be specified manually, like below.
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

        self.action = "image_policy_attach"
        self.diff: dict = {}
        self.payloads = []
        self.saved_response_current: dict = {}
        self.saved_result_current: dict = {}

        self.ep_policy_attach = EpPolicyAttach()
        self.image_policies = ImagePolicies()
        self.switch_issu_details = SwitchIssuDetailsBySerialNumber()
        self.wait_for_controller_done = WaitForControllerDone()

        self._check_interval = 10  # seconds
        self._check_timeout = 1800  # seconds
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

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.payloads = []

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
                    raise ValueError(msg)
            self.payloads.append(payload)

    def validate_commit_parameters(self):
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

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit()."
            raise ValueError(msg)

        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling commit()."
            raise ValueError(msg)

        if self.serial_numbers is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.serial_numbers must be set before "
            msg += "calling commit()"
            raise ValueError(msg)

    def validate_image_policies(self):
        """
        ### Summary
        Validate that the image policy exists on the controller
        and supports the switch platform.

        ### Raises
        -   ValueError: if:
                -   ``policy_name`` does not exist on the controller.
                -   ``policy_name`` does not support the switch platform.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

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

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        try:
            self.validate_commit_parameters()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while validating commit parameters. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.switch_issu_details.rest_send = self.rest_send
        # Don't include results in user output.
        self.switch_issu_details.results = Results()

        self.image_policies.results = Results()
        self.image_policies.rest_send = self.rest_send  # pylint: disable=no-member

        try:
            self.validate_image_policies()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while validating image policies. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.wait_for_controller()
        self.attach_policy()

    def wait_for_controller(self):
        """
        ### Summary
        Wait for any actions on the controller to complete.

        ### Raises
        -   ValueError: if:
                -   ``items`` is not a set.
                -   ``item_type`` is not a valid item type.
                -   The action times out.
        """
        method_name = inspect.stack()[0][3]
        try:
            self.wait_for_controller_done.items = set(copy.copy(self.serial_numbers))
            self.wait_for_controller_done.item_type = "serial_number"
            self.wait_for_controller_done.rest_send = (
                self.rest_send  # pylint: disable=no-member
            )
            self.wait_for_controller_done.commit()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Error {error}."
            raise ValueError(msg) from error

    def build_diff(self):
        """
        ### Summary
        Build the diff for the task result.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.diff: dict = {}
        for payload in self.payloads:
            ipv4 = payload["ipAddr"]
            if ipv4 not in self.diff:
                self.diff[ipv4] = {}
            self.diff[ipv4]["action"] = self.action
            self.diff[ipv4]["ip_address"] = payload["ipAddr"]
            self.diff[ipv4]["logical_name"] = payload["hostName"]
            self.diff[ipv4]["policy_name"] = payload["policyName"]
            self.diff[ipv4]["serial_number"] = payload["serialNumber"]

    def attach_policy(self):
        """
        ### Summary
        Attach policy_name to the switch(es) associated with serial_numbers.

        ### Raises
        -   ValueError: if the result of the POST request is not successful.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.build_payload()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"rest_send.check_mode: {self.rest_send.check_mode}"
        self.log.debug(msg)

        payload: dict = {}
        payload["mappingList"] = self.payloads
        self.rest_send.payload = payload
        self.rest_send.path = self.ep_policy_attach.path
        self.rest_send.verb = self.ep_policy_attach.verb
        self.rest_send.commit()

        msg = f"result_current: {json.dumps(self.rest_send.result_current, indent=4)}"
        self.log.debug(msg)
        msg = (
            f"response_current: {json.dumps(self.rest_send.response_current, indent=4)}"
        )
        self.log.debug(msg)

        self.build_diff()
        self.results.action = self.action
        self.results.diff_current = copy.deepcopy(self.diff)
        self.results.result_current = self.rest_send.result_current
        self.results.response_current = self.rest_send.response_current
        self.results.register_task_result()

        if not self.rest_send.result_current["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Bad result when attaching policy {self.policy_name} "
            msg += f"to switch. Payload: {payload}."
            raise ValueError(msg)

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
            raise TypeError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.serial_numbers must contain at least one "
            msg += "switch serial number."
            raise ValueError(msg)
        self._serial_numbers = value

    @property
    def check_interval(self):
        """
        ### Summary
        The validate check interval, in seconds.

        ### Raises
        -   ``TypeError`` if the value is not an integer.
        -   ``ValueError`` if the value is less than zero.
        """
        return self._check_interval

    @check_interval.setter
    def check_interval(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "must be a positive integer or zero. "
        msg += f"Got value {value} of type {type(value)}."
        # isinstance(True, int) is True so we need to check for bool first
        if isinstance(value, bool):
            raise TypeError(msg)
        if not isinstance(value, int):
            raise TypeError(msg)
        if value < 0:
            raise ValueError(msg)
        self._check_interval = value

    @property
    def check_timeout(self):
        """
        ### Summary
        The validate check timeout, in seconds.

        ### Raises
        -   ``TypeError`` if the value is not an integer.
        -   ``ValueError`` if the value is less than zero.
        """
        return self._check_timeout

    @check_timeout.setter
    def check_timeout(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "must be a positive integer or zero. "
        msg += f"Got value {value} of type {type(value)}."
        # isinstance(True, int) is True so we need to check for bool first
        if isinstance(value, bool):
            raise TypeError(msg)
        if not isinstance(value, int):
            raise TypeError(msg)
        if value < 0:
            raise ValueError(msg)
        self._check_timeout = value
