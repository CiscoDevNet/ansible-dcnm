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
from time import sleep

from ..common.api.v1.imagemanagement.rest.stagingmanagement.stagingmanagement import \
    EpImageValidate
from ..common.conversion import ConversionUtils
from ..common.exceptions import ControllerResponseError
from ..common.properties import Properties
from ..common.results import Results
from .switch_issu_details import SwitchIssuDetailsBySerialNumber
from .wait_for_controller_done import WaitForControllerDone


@Properties.add_rest_send
@Properties.add_results
class ImageValidate:
    """
    ### Summary
    Validate an image on a switch.

    ### Endpoint
    -   path: /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/validate-image
    -   verb: POST

    ### Usage example

    ```python
    # params is typically obtained from ansible_module.params
    # but can also be specified manually, like below.
    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    results = Results()

    instance = ImageValidate()
    # mandatory parameters
    instance.rest_send = rest_send
    instance.results = results
    instance.serial_numbers = ["FDO211218HH", "FDO211218GC"]
    instance.commit()
    ```

    ### Request body
    ```json
    {
        "serialNum": ["FDO21120U5D"],
        "nonDisruptive":"true"
    }
    ```

    ### Response body when nonDisruptive is True:
    ```
    [StageResponse [key=success, value=]]
    ```

    ### Response body when nonDisruptive is False:
    ```
    [StageResponse [key=success, value=]]
    ```

    The response is not JSON, nor is it very useful. Instead, we poll for
    validation status using ``SwitchIssuDetailsBySerialNumber``.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action = "image_validate"
        self.diff: dict = {}
        self.payload = None
        self.saved_response_current: dict = {}
        self.saved_result_current: dict = {}
        # _wait_for_image_validate_to_complete() populates these
        self.serial_numbers_done: set = set()
        self.serial_numbers_todo = set()

        self.conversion = ConversionUtils()
        self.ep_image_validate = EpImageValidate()
        self.issu_detail = SwitchIssuDetailsBySerialNumber()
        self.wait_for_controller_done = WaitForControllerDone()

        self._check_interval = 10  # seconds
        self._check_timeout = 1800  # seconds
        self._non_disruptive = False
        self._rest_send = None
        self._results = None
        self._serial_numbers = None

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def build_diff(self) -> None:
        """
        ### Summary
        Build the diff of the image validate operation.

        ### Raises
        None
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.diff: dict = {}

        for serial_number in self.serial_numbers_done:
            self.issu_detail.filter = serial_number
            ipv4 = self.issu_detail.ip_address

            if ipv4 not in self.diff:
                self.diff[ipv4] = {}

            self.diff[ipv4]["action"] = self.action
            self.diff[ipv4]["ip_address"] = self.issu_detail.ip_address
            self.diff[ipv4]["logical_name"] = self.issu_detail.device_name
            self.diff[ipv4]["policy_name"] = self.issu_detail.policy
            self.diff[ipv4]["serial_number"] = serial_number
            msg = f"{self.class_name}.{method_name}: "
            msg += f"self.diff[{ipv4}]: "
            msg += f"{json.dumps(self.diff[ipv4], indent=4)}"
            self.log.debug(msg)

    def build_payload(self) -> None:
        """
        Build the payload for the image validation request
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"self.serial_numbers: {self.serial_numbers}"
        self.log.debug(msg)

        self.payload = {}
        self.payload["serialNum"] = self.serial_numbers
        self.payload["nonDisruptive"] = self.non_disruptive

    def prune_serial_numbers(self) -> None:
        """
        If the image is already validated on a switch, remove that switch's
        serial number from the list of serial numbers to validate.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}: "
        msg += f"self.serial_numbers {self.serial_numbers}"
        self.log.debug(msg)

        self.issu_detail.refresh()
        serial_numbers = copy.copy(self.serial_numbers)
        for serial_number in serial_numbers:
            self.issu_detail.filter = serial_number
            if self.issu_detail.validated == "Success":
                self.serial_numbers.remove(self.issu_detail.serial_number)

        msg = f"DONE: self.serial_numbers {self.serial_numbers}"
        self.log.debug(msg)

    def register_unchanged_result(self, response_message) -> None:
        """
        ### Summary
        Register a successful unchanged result with the results object.
        """
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

        self.results.action = self.action
        self.results.diff_current = {}
        self.results.response_current = {"response": response_message}
        self.results.result_current = {"success": True, "changed": False}
        self.results.response_data = {"response": response_message}
        self.results.register_task_result()

    def validate_serial_numbers(self) -> None:
        """
        ### Summary
        Fail if "validated" is "Failed" for any serial number.

        ### Raises
        -   ``ControllerResponseError`` if:
                -   "validated" is "Failed" for any serial_number.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"self.serial_numbers: {self.serial_numbers}"
        self.log.debug(msg)

        self.issu_detail.refresh()
        for serial_number in self.serial_numbers:
            self.issu_detail.filter = serial_number
            if self.issu_detail.validated == "Failed":
                msg = f"{self.class_name}.{method_name}: "
                msg += "image validation is failing for the following switch: "
                msg += f"{self.issu_detail.device_name}, "
                msg += f"{self.issu_detail.ip_address}, "
                msg += f"{self.issu_detail.serial_number}. "
                msg += "If this persists, check the switch connectivity to "
                msg += "the controller and try again."
                raise ControllerResponseError(msg)

    def validate_commit_parameters(self) -> None:
        """
        ### Summary
        Verify mandatory parameters are set before calling commit.

        ### Raises
        -   ``ValueError`` if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
                -   ``serial_numbers`` is not set.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        # pylint: disable=no-member
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit()."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling commit()."
            raise ValueError(msg)
        # pylint: enable=no-member
        if self.serial_numbers is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "serial_numbers must be set before calling commit()."
            raise ValueError(msg)

    def commit(self) -> None:
        """
        ### Summary
        Commit the image validation request to the controller and wait
        for the images to be validated.

        ### Raises
        -   ``ValueError`` if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
                -   ``serial_numbers`` is not set.
        -   ``ControllerResponseError`` if:
                -   The controller response is unsuccessful.
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.serial_numbers: {self.serial_numbers}"
        self.log.debug(msg)

        self.validate_commit_parameters()

        if len(self.serial_numbers) == 0:
            msg = "No images to validate."
            self.register_unchanged_result(msg)
            return

        # pylint: disable=no-member
        self.issu_detail.rest_send = self.rest_send
        # pylint: enable=no-member
        # We don't want the results to show up in the user's result output.
        self.issu_detail.results = Results()

        self.prune_serial_numbers()
        self.validate_serial_numbers()
        self.wait_for_controller()
        self.build_payload()

        msg = f"{self.class_name}.{method_name}: "
        msg += "Calling RestSend().commit()"
        self.log.debug(msg)

        # pylint: disable=no-member
        try:
            self.rest_send.verb = self.ep_image_validate.verb
            self.rest_send.path = self.ep_image_validate.path
            self.rest_send.payload = self.payload
            self.rest_send.commit()
        except (TypeError, ValueError) as error:
            self.results.diff_current = {}
            self.results.action = self.action
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while sending request. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        if not self.rest_send.result_current["success"]:
            self.results.diff_current = {}
            self.results.action = self.action
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()
            msg = f"{self.class_name}.{method_name}: "
            msg += "failed. "
            msg += f"Controller response: {self.rest_send.response_current}"
            raise ControllerResponseError(msg)

        # Save response_current and result_current so they aren't overwritten
        # by _wait_for_image_validate_to_complete(), which needs to run
        # before we can build the diff, since the diff is based on the
        # serial_numbers_done set, which isn't populated until image
        # validate is complete.
        self.saved_response_current = copy.deepcopy(self.rest_send.response_current)
        self.saved_result_current = copy.deepcopy(self.rest_send.result_current)

        self._wait_for_image_validate_to_complete()

        self.build_diff()
        self.results.action = self.action
        self.results.diff_current = copy.deepcopy(self.diff)
        self.results.response_current = copy.deepcopy(self.saved_response_current)
        self.results.result_current = copy.deepcopy(self.saved_result_current)
        self.results.register_task_result()

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

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

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

    def _wait_for_image_validate_to_complete(self) -> None:
        """
        ### Summary
        Wait for image validation to complete.

        ### Raises
        -   ``ValueError`` if:
                -   The image validation does not complete within the timeout.
                -   The image validation fails.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.serial_numbers_done = set()
        timeout = self.check_timeout
        self.serial_numbers_todo = set(copy.copy(self.serial_numbers))

        while self.serial_numbers_done != self.serial_numbers_todo and timeout > 0:
            if self.rest_send.unit_test is False:  # pylint: disable=no-member
                sleep(self.check_interval)
            timeout -= self.check_interval
            self.issu_detail.refresh()

            for serial_number in self.serial_numbers:
                if serial_number in self.serial_numbers_done:
                    continue

                self.issu_detail.filter = serial_number

                ip_address = self.issu_detail.ip_address
                device_name = self.issu_detail.device_name
                validated_percent = self.issu_detail.validated_percent
                validated_status = self.issu_detail.validated

                if validated_status == "Failed":
                    msg = f"{self.class_name}.{method_name}: "
                    msg = f"Seconds remaining {timeout}: validate image "
                    msg += f"{validated_status} for "
                    msg += f"{device_name}, {ip_address}, {serial_number}, "
                    msg += f"image validated percent: {validated_percent}. "
                    msg += "Check the switch e.g. show install log detail, "
                    msg += "show incompatibility-all nxos <image>.  Or "
                    msg += "check Operations > Image Management > "
                    msg += "Devices > View Details > Validate on the "
                    msg += "controller GUI for more details."
                    raise ValueError(msg)
                if validated_status == "Success":
                    self.serial_numbers_done.add(serial_number)

            msg = f"seconds remaining {timeout}"
            self.log.debug(msg)
            msg = f"serial_numbers_todo: {sorted(self.serial_numbers_todo)}"
            self.log.debug(msg)
            msg = f"serial_numbers_done: {sorted(self.serial_numbers_done)}"
            self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += "Completed. "
        msg += f"serial_numbers_done: {sorted(self.serial_numbers_done)}."
        self.log.debug(msg)

        if self.serial_numbers_done != self.serial_numbers_todo:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Timed out waiting for image validation to complete. "
            msg += "serial_numbers_done: "
            msg += f"{','.join(sorted(self.serial_numbers_done))}, "
            msg += "serial_numbers_todo: "
            msg += f"{','.join(sorted(self.serial_numbers_todo))}"
            raise ValueError(msg)

    @property
    def response_data(self) -> dict:
        """
        ### Summary
        Return the DATA key of the controller response.
        Obtained from self.rest_send.response_current.

        commit must be called before accessing this property.
        """
        # pylint: disable=no-member
        return self.rest_send.response_current.get("DATA")

    @property
    def serial_numbers(self) -> list:
        """
        ### Summary
        A ``list`` of switch serial numbers.  The image will be validated on
        each switch in the list.

        ``serial_numbers`` must be set before calling commit.

        ### Raises
        -   ``TypeError`` if value is not a list of serial numbers.
        """
        return self._serial_numbers

    @serial_numbers.setter
    def serial_numbers(self, value) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "must be a python list of switch serial numbers."
            raise TypeError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "must be a python list of switch serial numbers."
                raise TypeError(msg)
        self._serial_numbers = value

    @property
    def non_disruptive(self) -> bool:
        """
        ### Summary
        Set the non_disruptive flag to True or False.

        ### Raises
        -   ``TypeError`` if the value is not a boolean.
        """
        return self._non_disruptive

    @non_disruptive.setter
    def non_disruptive(self, value) -> None:
        method_name = inspect.stack()[0][3]

        value = self.conversion.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.non_disruptive must be a boolean. "
            msg += f"Got {value}."
            raise TypeError(msg)

        self._non_disruptive = value

    @property
    def check_interval(self) -> int:
        """
        ### Summary
        The validate check interval, in seconds.

        ### Raises
        -   ``TypeError`` if the value is not an integer.
        -   ``ValueError`` if the value is less than zero.
        """
        return self._check_interval

    @check_interval.setter
    def check_interval(self, value) -> None:
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
    def check_timeout(self) -> int:
        """
        ### Summary
        The validate check timeout, in seconds.

        ### Raises
        -   ``TypeError`` if the value is not an integer.
        -   ``ValueError`` if the value is less than zero.
        """
        return self._check_timeout

    @check_timeout.setter
    def check_timeout(self, value) -> None:
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
