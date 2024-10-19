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

from ..common.api.v1.imagemanagement.rest.policymgnt.policymgnt import EpPolicyDetach
from ..common.exceptions import ControllerResponseError
from ..common.image_policies import ImagePolicies
from ..common.properties import Properties
from ..common.results import Results
from .switch_issu_details import SwitchIssuDetailsBySerialNumber
from .wait_for_controller_done import WaitForControllerDone


@Properties.add_rest_send
@Properties.add_results
class ImagePolicyDetach:
    """
    ### Summary
    Detach image policies from one or more switches.

    ### Raises
    -   ValueError: if:
            -   ``serial_numbers`` is not set before calling commit.
            -   ``serial_numbers`` is an empty list.
            -   The result of the DELETE request is not successful.
    -   TypeError: if:
            -   ``check_interval`` is not an integer.
            -   ``check_timeout`` is not an integer.
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

    instance = ImagePolicyDetach()
    instance.rest_send = rest_send
    instance.results = results
    instance.serial_numbers = ["FDO211218GC", "FDO211218HH"]
    instance.commit()
    ```

    ### Endpoint
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action = "image_policy_detach"
        self.diff: dict = {}
        self.saved_response_current: dict = {}
        self.saved_result_current: dict = {}

        self.ep_policy_detach = EpPolicyDetach()
        self.image_policies = ImagePolicies()
        self.switch_issu_details = SwitchIssuDetailsBySerialNumber()
        self.wait_for_controller_done = WaitForControllerDone()

        self._check_interval = 10  # seconds
        self._check_timeout = 1800  # seconds
        self._rest_send = None
        self._results = None

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def build_diff(self):
        """
        ### Summary
        Build the diff of the detach policy operation.

        ### Raises
        -   ValueError: if the switch is not managed by the controller.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.diff: dict = {}

        self.switch_issu_details.refresh()
        for serial_number in self.serial_numbers:
            self.switch_issu_details.filter = serial_number
            ipv4 = self.switch_issu_details.ip_address

            if ipv4 not in self.diff:
                self.diff[ipv4] = {}

            self.diff[ipv4]["action"] = self.action
            self.diff[ipv4]["policy_name"] = self.switch_issu_details.policy
            self.diff[ipv4]["device_name"] = self.switch_issu_details.device_name
            self.diff[ipv4]["ipv4_address"] = self.switch_issu_details.ip_address
            self.diff[ipv4]["platform"] = self.switch_issu_details.platform
            self.diff[ipv4]["serial_number"] = self.switch_issu_details.serial_number
            msg = f"{self.class_name}.{method_name}: "
            msg += f"self.diff[{ipv4}]: {json.dumps(self.diff[ipv4], indent=4)}"
            self.log.debug(msg)

    def validate_commit_parameters(self):
        """
        ### Summary
        Validations prior to commit() should be added here.

        ### Raises
        -   ValueError: if:
                -   ``serial_numbers`` is not set.
        """
        method_name = inspect.stack()[0][3]

        msg = "ENTERED"
        self.log.debug(msg)

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

    def commit(self):
        """
        ### Summary
        Attach image policy to switches.

        ### Raises
        -   ValueError: if:
                -   ``serial_numbers`` is not set.
                -   ``results`` is not set.
                -   ``rest_send`` is not set.
                -   Error encountered while waiting for controller actions
                    to complete.
                -   The result of the DELETE request is not successful.
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

        try:
            self.wait_for_controller()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

        try:
            self.detach_policy()
        except (ControllerResponseError, TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while detaching image policies from switches. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

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
        try:
            self.wait_for_controller_done.items = set(copy.copy(self.serial_numbers))
            self.wait_for_controller_done.item_type = "serial_number"
            self.wait_for_controller_done.rest_send = (
                self.rest_send  # pylint: disable=no-member
            )
            self.wait_for_controller_done.commit()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.wait_for_controller: "
            msg += "Error while waiting for controller actions to complete. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def detach_policy(self):
        """
        ### Summary
        Detach image policy from the switch(es) associated with
        ``serial_numbers``.

        ### Raises
        -   ``ControllerResponseError`` if:
                -   The result of the DELETE request is not successful.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.ep_policy_detach.serial_numbers = self.serial_numbers

        msg = f"{self.class_name}.{method_name}: "
        msg += "ep_policy_detach: "
        msg += f"verb: {self.ep_policy_detach.verb}, "
        msg += f"path: {self.ep_policy_detach.path}"
        self.log.debug(msg)

        # Build the diff before sending the request so that
        # we can include the policy names in the diff.
        self.build_diff()

        self.rest_send.path = self.ep_policy_detach.path
        self.rest_send.verb = self.ep_policy_detach.verb
        self.rest_send.commit()

        msg = f"result_current: {json.dumps(self.rest_send.result_current, indent=4)}"
        self.log.debug(msg)

        msg = "response_current: "
        msg += f"{json.dumps(self.rest_send.response_current, indent=4)}"
        self.log.debug(msg)

        self.results.action = self.action
        self.results.diff_current = self.diff
        self.results.response_current = self.rest_send.response_current
        self.results.result_current = self.rest_send.result_current
        self.results.register_task_result()

        if not self.rest_send.result_current["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Bad result when detaching image polices from switches: "
            msg += f"{','.join(self.serial_numbers)}."
            raise ControllerResponseError(msg)

    @property
    def serial_numbers(self):
        """
        ### Summary
        Set the serial numbers of the switches from which
        image policies will be detached.

        Must be set prior to calling ``commit``.

        ### Raises
        -   ``TypeError`` if value is not a list.
        -   ``ValueError`` if value is an empty list.
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
