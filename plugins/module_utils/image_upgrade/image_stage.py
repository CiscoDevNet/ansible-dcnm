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
    EpImageStage
from ..common.controller_version import ControllerVersion
from ..common.exceptions import ControllerResponseError
from ..common.properties import Properties
from ..common.results import Results
from .switch_issu_details import SwitchIssuDetailsBySerialNumber
from .wait_for_controller_done import WaitForControllerDone


@Properties.add_rest_send
@Properties.add_results
class ImageStage:
    """
    ### Summary
    Stage an image on a set of switches.

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

    instance = ImageStage()
    # mandatory parameters
    instance.rest_send = rest_send
    instance.results = results
    instance.serial_numbers = ["FDO211218HH", "FDO211218GC"]
    instance.commit()
    ```

    ### Request body (12.1.2e) (yes, serialNum is misspelled)

    ```json
        {
            "sereialNum": [
                "FDO211218HH",
                "FDO211218GC"
            ]
        }
    ```

    ### Request body (12.1.3b):
    ```json
        {
            "serialNumbers": [
                "FDO211218HH",
                "FDO211218GC"
            ]
        }
    ```

    ### Response
    Unfortunately, the response does not contain consistent data.
    Would be better if all responses contained serial numbers as keys so that
    we could verify against a set() of serial numbers.

    ```json
        {
            "RETURN_CODE": 200,
            "METHOD": "POST",
            "REQUEST_PATH": ".../api/v1/imagemanagement/rest/stagingmanagement/stage-image",
            "MESSAGE": "OK",
            "DATA": [
                {
                    "key": "success",
                    "value": ""
                },
                {
                    "key": "success",
                    "value": ""
                }
            ]
        }
    ```

    ### Response when there are no files to stage
    ```json
        [
            {
                "key": "FDO211218GC",
                "value": "No files to stage"
            },
            {
                "key": "FDO211218HH",
                "value": "No files to stage"
            }
        ]
    ```

    ### Endpoint Path
    ```
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image
    ```

    ### Endpoint Verb
    ``POST``

    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action = "image_stage"
        self.controller_version = None
        self.diff: dict = {}
        self.payload = None
        self.saved_response_current: dict = {}
        self.saved_result_current: dict = {}
        # _wait_for_image_stage_to_complete() populates these
        self.serial_numbers_done = set()
        self.serial_numbers_todo = set()

        self.controller_version_instance = ControllerVersion()
        self.ep_image_stage = EpImageStage()
        self.issu_detail = SwitchIssuDetailsBySerialNumber()
        self.wait_for_controller_done = WaitForControllerDone()

        self._check_interval = 10  # seconds
        self._check_timeout = 1800  # seconds
        self._rest_send = None
        self._results = None
        self._serial_numbers = None

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def build_diff(self) -> None:
        """
        ### Summary
        Build the diff of the image stage operation.

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

    def _populate_controller_version(self) -> None:
        """
        Populate self.controller_version with the running controller version.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

        self.controller_version_instance.refresh()
        self.controller_version = self.controller_version_instance.version

    def prune_serial_numbers(self) -> None:
        """
        If the image is already staged on a switch, remove that switch's
        serial number from the list of serial numbers to stage.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}: "
        msg += f"self.serial_numbers {self.serial_numbers}"
        self.log.debug(msg)

        serial_numbers = copy.copy(self.serial_numbers)
        self.issu_detail.refresh()
        for serial_number in serial_numbers:
            self.issu_detail.filter = serial_number
            if self.issu_detail.image_staged == "Success":
                self.serial_numbers.remove(serial_number)

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
        self.results.check_mode = self.rest_send.check_mode
        self.results.diff_current = {}
        self.results.response_current = {
            "DATA": [{"key": "ALL", "value": response_message}]
        }
        self.results.result_current = {"success": True, "changed": False}
        self.results.response_data = {"response": response_message}
        self.results.state = self.rest_send.state
        self.results.register_task_result()

    def validate_serial_numbers(self) -> None:
        """
        ### Summary
        Fail if "imageStaged" is "Failed" for any serial number.

        ### Raises
        -   ``ControllerResponseError`` if:
                -   "imageStaged" is "Failed" for any serial_number.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"self.serial_numbers: {self.serial_numbers}"
        self.log.debug(msg)

        self.issu_detail.refresh()
        for serial_number in self.serial_numbers:
            self.issu_detail.filter = serial_number

            if self.issu_detail.image_staged == "Failed":
                msg = f"{self.class_name}.{method_name}: "
                msg = "Image staging is failing for the following switch: "
                msg += f"{self.issu_detail.device_name}, "
                msg += f"{self.issu_detail.ip_address}, "
                msg += f"{self.issu_detail.serial_number}. "
                msg += "Check the switch connectivity to the controller "
                msg += "and try again."
                raise ControllerResponseError(msg)

    def validate_commit_parameters(self) -> None:
        """
        Verify mandatory parameters are set before calling commit.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}().{method_name}"
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

    def build_payload(self) -> None:
        """
        ### Summary
        Build the payload for the image stage request.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

        self.payload = {}
        self._populate_controller_version()

        if self.controller_version == "12.1.2e":
            # Yes, version 12.1.2e wants serialNum to be misspelled
            self.payload["sereialNum"] = self.serial_numbers
        else:
            self.payload["serialNumbers"] = self.serial_numbers

    def commit(self) -> None:
        """
        ### Summary
        Commit the image staging request to the controller and wait
        for the images to be staged.

        ### Raises
        -   ``ValueError`` if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
                -   ``serial_numbers`` is not set.
        -   ``ControllerResponseError`` if:
                -   The controller response is unsuccessful.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.serial_numbers: {self.serial_numbers}"
        self.log.debug(msg)

        self.validate_commit_parameters()

        if len(self.serial_numbers) == 0:
            msg = "No images to stage."
            self.register_unchanged_result(msg)
            return

        # pylint: disable=no-member
        self.issu_detail.rest_send = self.rest_send
        self.controller_version_instance.rest_send = self.rest_send
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
            self.rest_send.verb = self.ep_image_stage.verb
            self.rest_send.path = self.ep_image_stage.path
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
        # by _wait_for_image_stage_to_complete(), which needs to run
        # before we can build the diff, since the diff is based on the
        # serial_numbers_done set, which isn't populated until image
        # stage is complete.
        self.saved_response_current = copy.deepcopy(self.rest_send.response_current)
        self.saved_result_current = copy.deepcopy(self.rest_send.result_current)

        self._wait_for_image_stage_to_complete()
        self.build_diff()

        self.results.action = self.action
        self.results.diff_current = copy.deepcopy(self.diff)
        self.results.response_current = copy.deepcopy(self.saved_response_current)
        self.results.result_current = copy.deepcopy(self.saved_result_current)
        self.results.register_task_result()

    def wait_for_controller(self) -> None:
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
            msg = f"{self.class_name}.wait_for_controller: "
            msg += "Error while waiting for controller actions to complete. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def _wait_for_image_stage_to_complete(self) -> None:
        """
        ### Summary
        Wait for image stage to complete

        ### Raises
        -   ``ValueError`` if:
                -   Image stage does not complete within ``check_timeout``
                    seconds.
                -   Image stage fails for any switch.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}().{method_name}"
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
                staged_percent = self.issu_detail.image_staged_percent
                staged_status = self.issu_detail.image_staged

                if staged_status == "Failed":
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f"Seconds remaining {timeout}: stage image failed "
                    msg += f"for {device_name}, {serial_number}, {ip_address}. "
                    msg += f"image staged percent: {staged_percent}"
                    raise ValueError(msg)
                if staged_status == "Success":
                    self.serial_numbers_done.add(serial_number)

            msg = f"seconds remaining {timeout}"
            self.log.debug(msg)
            msg = f"serial_numbers_todo: {sorted(self.serial_numbers_todo)}"
            self.log.debug(msg)
            msg = f"serial_numbers_done: {sorted(self.serial_numbers_done)}"
            self.log.debug(msg)

        if self.serial_numbers_done != self.serial_numbers_todo:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Timed out waiting for image stage to complete. "
            msg += "serial_numbers_done: "
            msg += f"{','.join(sorted(self.serial_numbers_done))}, "
            msg += "serial_numbers_todo: "
            msg += f"{','.join(sorted(self.serial_numbers_todo))}"
            raise ValueError(msg)

    @property
    def serial_numbers(self) -> list:
        """
        ### Summary
        Set the serial numbers of the switches to stage.

        This must be set before calling instance.commit()

        ### Raises
        -   ``TypeError`` if:
                -   value is not a list of switch serial numbers.
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
    def check_interval(self) -> int:
        """
        ### Summary
        The interval, in seconds, used to check the status of the image stage
        operation.  Used by ``_wait_for_image_stage_to_complete()``.

        ### Raises
        -   ``TypeError`` if:
                -   value is not a positive integer.
        -   ``ValueError`` if:
                -   value is an integer less than zero.
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
        The interval, in seconds, used to check the status of the image stage
        operation.  Used by ``_wait_for_image_stage_to_complete()``.

        ### Raises
        -   ``TypeError`` if:
                -   value is not a positive integer.
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
