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
from time import sleep

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.stagingmanagement.stagingmanagement import \
    EpImageStage
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_version import \
    ControllerVersion
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber


@Properties.add_params
@Properties.add_rest_send
@Properties.add_results
class ImageStage:
    """
    Endpoint:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image

    Verb: POST

    Usage (where module is an instance of AnsibleModule):

    stage = ImageStage(module)
    stage.serial_numbers = ["FDO211218HH", "FDO211218GC"]
    stage.commit()

    Request body (12.1.2e) (yes, serialNum is misspelled):
        {
            "sereialNum": [
                "FDO211218HH",
                "FDO211218GC"
            ]
        }
    Request body (12.1.3b):
        {
            "serialNumbers": [
                "FDO211218HH",
                "FDO211218GC"
            ]
        }

    Response:
        Unfortunately, the response does not contain consistent data.
        Would be better if all responses contained serial numbers as keys so that
        we could verify against a set() of serial numbers.
        {
            'RETURN_CODE': 200,
            'METHOD': 'POST',
            'REQUEST_PATH': '.../api/v1/imagemanagement/rest/stagingmanagement/stage-image',
            'MESSAGE': 'OK',
            'DATA': [
                {
                    'key': 'success',
                    'value': ''
                },
                {
                    'key': 'success',
                    'value': ''
                }
            ]
        }

        Response when there are no files to stage:
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
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.action = "image_stage"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.endpoint = EpImageStage()
        self.path = self.endpoint.path
        self.verb = self.endpoint.verb
        self.payload = None

        self.serial_numbers_done = set()
        self.controller_version = None
        self.issu_detail = SwitchIssuDetailsBySerialNumber()
        self._serial_numbers = None
        self._check_interval = 10  # seconds
        self._check_timeout = 1800  # seconds

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def _populate_controller_version(self):
        """
        Populate self.controller_version with the running controller version.
        """
        instance = ControllerVersion()
        instance.refresh()
        self.controller_version = instance.version

    def prune_serial_numbers(self):
        """
        If the image is already staged on a switch, remove that switch's
        serial number from the list of serial numbers to stage.
        """
        serial_numbers = copy.copy(self.serial_numbers)
        self.issu_detail.refresh()
        for serial_number in serial_numbers:
            self.issu_detail.filter = serial_number
            if self.issu_detail.image_staged == "Success":
                self.serial_numbers.remove(serial_number)

    def validate_serial_numbers(self):
        """
        ### Summary
        Fail if the image_staged state for any serial_number
        is Failed.

        ### Raises
        -   ``ControllerResponseError`` if:
                -   image_staged is Failed for any serial_number.
        """
        method_name = inspect.stack()[0][3]
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

    def commit(self) -> None:
        """
        ### Summary
        Commit the image staging request to the controller and wait
        for the images to be staged.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        msg = f"self.serial_numbers: {self.serial_numbers}"
        self.log.debug(msg)

        if self.serial_numbers is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "call instance.serial_numbers "
            msg += "before calling commit."
            raise ValueError(msg)

        if len(self.serial_numbers) == 0:
            msg = "No files to stage."
            response_current = {"DATA": [{"key": "ALL", "value": msg}]}
            self.results.response_current = response_current
            self.results.diff_current = {}
            self.results.action = self.action
            self.results.check_mode = self.params.get("check_mode")
            self.results.state = self.params.get("state")
            self.results.result_current = self.results.ok_result
            self.results.register_task_result()
            return

        self.prune_serial_numbers()
        self.validate_serial_numbers()
        self._wait_for_current_actions_to_complete()

        self.payload = {}
        self._populate_controller_version()

        if self.controller_version == "12.1.2e":
            # Yes, version 12.1.2e wants serialNum to be misspelled
            self.payload["sereialNum"] = self.serial_numbers
        else:
            self.payload["serialNumbers"] = self.serial_numbers

        try:
            self.rest_send.verb = self.verb
            self.rest_send.path = self.path
            self.rest_send.payload = self.payload
            self.rest_send.commit()
        except (TypeError, ValueError) as error:
            self.results.diff_current = {}
            self.results.action = self.action
            self.results.check_mode = self.params.get("check_mode")
            self.results.state = self.params.get("state")
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while sending request. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        if self.rest_send.result_current["success"] is False:
            self.results.diff_current = {}
        else:
            self.results.diff_current = copy.deepcopy(self.payload)

        self.results.action = self.action
        self.results.check_mode = self.params.get("check_mode")
        self.results.response_current = copy.deepcopy(self.rest_send.response_current)
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.state = self.params.get("state")
        self.results.register_task_result()

        if not self.rest_send.result_current["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"failed: {self.rest_send.result_current}. "
            msg += f"Controller response: {self.rest_send.response_current}"
            raise ValueError(msg)

        self._wait_for_image_stage_to_complete()

        for serial_number in self.serial_numbers_done:
            self.issu_detail.filter = serial_number
            diff = {}
            diff["action"] = "stage"
            diff["ip_address"] = self.issu_detail.ip_address
            diff["logical_name"] = self.issu_detail.device_name
            diff["policy"] = self.issu_detail.policy
            diff["serial_number"] = serial_number

            self.results.action = self.action
            self.results.check_mode = self.params.get("check_mode")
            self.results.diff_current = copy.deepcopy(diff)
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.state = self.params.get("state")
            self.results.register_task_result()

    def _wait_for_current_actions_to_complete(self):
        """
        The controller will not stage an image if there are any actions in
        progress.  Wait for all actions to complete before staging image.
        Actions include image staging, image upgrade, and image validation.
        """
        method_name = inspect.stack()[0][3]

        self.serial_numbers_done = set()
        serial_numbers_todo = set(copy.copy(self.serial_numbers))
        timeout = self.check_timeout

        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
            if self.unit_test is False:
                sleep(self.check_interval)
            timeout -= self.check_interval
            self.issu_detail.refresh()

            for serial_number in self.serial_numbers:
                if serial_number in self.serial_numbers_done:
                    continue

                self.issu_detail.filter = serial_number

                if self.issu_detail.actions_in_progress is False:
                    self.serial_numbers_done.add(serial_number)

        if self.serial_numbers_done != serial_numbers_todo:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Timed out waiting for actions to complete. "
            msg += "serial_numbers_done: "
            msg += f"{','.join(sorted(self.serial_numbers_done))}, "
            msg += "serial_numbers_todo: "
            msg += f"{','.join(sorted(serial_numbers_todo))}"
            raise ValueError(msg)

    def _wait_for_image_stage_to_complete(self):
        """
        # Wait for image stage to complete
        """
        method_name = inspect.stack()[0][3]

        self.serial_numbers_done = set()
        timeout = self.check_timeout
        serial_numbers_todo = set(copy.copy(self.serial_numbers))

        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
            if self.unit_test is False:
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
                msg = f"serial_numbers_todo: {sorted(serial_numbers_todo)}"
                self.log.debug(msg)
                msg = f"serial_numbers_done: {sorted(self.serial_numbers_done)}"
                self.log.debug(msg)

        if self.serial_numbers_done != serial_numbers_todo:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Timed out waiting for image stage to complete. "
            msg += "serial_numbers_done: "
            msg += f"{','.join(sorted(self.serial_numbers_done))}, "
            msg += "serial_numbers_todo: "
            msg += f"{','.join(sorted(serial_numbers_todo))}"
            raise ValueError(msg)

    @property
    def serial_numbers(self):
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
    def serial_numbers(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "must be a python list of switch serial numbers."
            raise TypeError(msg)
        self._serial_numbers = value

    @property
    def check_interval(self):
        """
        ### Summary
        The stage check interval, in seconds.

        ### Raises
        -   ``TypeError`` if:
                -   value is not a positive integer.
        -   ``ValueError`` if:
                -   value is an integer less than zero.
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
        The stage check timeout, in seconds.

        ### Raises
        -   ``TypeError`` if:
                -   value is not a positive integer.
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
