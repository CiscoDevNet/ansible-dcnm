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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_version import \
    ControllerVersion
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber


class ImageStage(ImageUpgradeCommon):
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

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImageStage()")

        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.module)
        self._init_properties()
        self.serial_numbers_done = set()
        self.controller_version = None
        self.path = None
        self.verb = None
        self.payload = None
        self.issu_detail = SwitchIssuDetailsBySerialNumber(self.module)

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        self.properties["serial_numbers"] = None
        self.properties["check_interval"] = 10  # seconds
        self.properties["check_timeout"] = 1800  # seconds

    def _populate_controller_version(self):
        """
        Populate self.controller_version with the running controller version.

        Notes:
        1.  This cannot go into ImageUpgradeCommon() due to circular
            imports resulting in RecursionError
        """
        instance = ControllerVersion(self.module)
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
        Fail if the image_staged state for any serial_number
        is Failed.
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
                self.module.fail_json(msg, **self.failed_result)

    def commit(self):
        """
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
            self.module.fail_json(msg, **self.failed_result)

        if len(self.serial_numbers) == 0:
            msg = "No files to stage."
            response_current = {"DATA": [{"key": "ALL", "value": msg}]}
            self.response_current = response_current
            self.response = response_current
            self.response_data = response_current.get("DATA", "No Stage DATA")
            self.result = {"changed": False, "success": True}
            self.result_current = {"changed": False, "success": True}
            return

        self.prune_serial_numbers()
        self.validate_serial_numbers()
        self._wait_for_current_actions_to_complete()

        self.path = self.endpoints.image_stage.get("path")
        self.verb = self.endpoints.image_stage.get("verb")

        self.payload = {}
        self._populate_controller_version()

        if self.controller_version == "12.1.2e":
            # Yes, version 12.1.2e wants serialNum to be misspelled
            self.payload["sereialNum"] = self.serial_numbers
        else:
            self.payload["serialNumbers"] = self.serial_numbers

        self.rest_send.verb = self.verb
        self.rest_send.path = self.path
        self.rest_send.payload = self.payload

        self.rest_send.commit()

        self.response = self.rest_send.response_current
        self.response_current = self.rest_send.response_current
        self.response_data = self.response_current.get("DATA", "No Stage DATA")

        self.result = self.rest_send.result_current
        self.result_current = self.rest_send.result_current

        msg = f"payload: {json.dumps(self.payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        msg = f"response: {json.dumps(self.response, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        msg = f"result: {json.dumps(self.result, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        msg = f"self.response_data: {self.response_data}"
        self.log.debug(msg)

        if not self.result_current["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"failed: {self.result_current}. "
            msg += f"Controller response: {self.response_current}"
            self.module.fail_json(msg, **self.failed_result)

        self._wait_for_image_stage_to_complete()

        for serial_number in self.serial_numbers_done:
            self.issu_detail.filter = serial_number
            diff = {}
            diff["action"] = "stage"
            diff["ip_address"] = self.issu_detail.ip_address
            diff["logical_name"] = self.issu_detail.device_name
            diff["policy"] = self.issu_detail.policy
            diff["serial_number"] = serial_number
            # See image_upgrade_common.py for the definition of self.diff
            self.diff = copy.deepcopy(diff)

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
            self.module.fail_json(msg, **self.failed_result)

    def _wait_for_image_stage_to_complete(self):
        """
        # Wait for image stage to complete
        """
        method_name = inspect.stack()[0][3]

        self.serial_numbers_done = set()
        timeout = self.check_timeout
        serial_numbers_todo = set(copy.copy(self.serial_numbers))

        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
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
                    self.module.fail_json(msg, **self.failed_result)

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
            self.module.fail_json(msg, **self.failed_result)

    @property
    def serial_numbers(self):
        """
        Set the serial numbers of the switches to stage.

        This must be set before calling instance.commit()
        """
        return self.properties.get("serial_numbers")

    @serial_numbers.setter
    def serial_numbers(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "must be a python list of switch serial numbers."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["serial_numbers"] = value

    @property
    def check_interval(self):
        """
        Return the stage check interval in seconds
        """
        return self.properties.get("check_interval")

    @check_interval.setter
    def check_interval(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "must be a positive integer or zero. "
        msg += f"Got value {value} of type {type(value)}."
        # isinstance(True, int) is True so we need to check for bool first
        if isinstance(value, bool):
            self.module.fail_json(msg, **self.failed_result)
        if not isinstance(value, int):
            self.module.fail_json(msg, **self.failed_result)
        if value < 0:
            self.module.fail_json(msg, **self.failed_result)
        self.properties["check_interval"] = value

    @property
    def check_timeout(self):
        """
        Return the stage check timeout in seconds
        """
        return self.properties.get("check_timeout")

    @check_timeout.setter
    def check_timeout(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "must be a positive integer or zero. "
        msg += f"Got value {value} of type {type(value)}."
        # isinstance(True, int) is True so we need to check for bool first
        if isinstance(value, bool):
            self.module.fail_json(msg, **self.failed_result)
        if not isinstance(value, int):
            self.module.fail_json(msg, **self.failed_result)
        if value < 0:
            self.module.fail_json(msg, **self.failed_result)
        self.properties["check_timeout"] = value
