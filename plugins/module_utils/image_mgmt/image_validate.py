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
from typing import List, Set

from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class ImageValidate(ImageUpgradeCommon):
    """
    Endpoint:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/validate-image

    Verb: POST

    Usage (where module is an instance of AnsibleModule):

    instance = ImageValidate(module)
    instance.serial_numbers = ["FDO211218HH", "FDO211218GC"]
    # non_disruptive is optional
    instance.non_disruptive = True
    instance.commit()
    data = instance.response_data

    Request body:
    {
        "serialNum": ["FDO21120U5D"],
        "nonDisruptive":"true"
    }

    Response body when nonDisruptive is True:
        [StageResponse [key=success, value=]]

    Response body when nonDisruptive is False:
        [StageResponse [key=success, value=]]

    The response is not JSON, nor is it very useful.
    Instead, we poll for validation status using
    SwitchIssuDetailsBySerialNumber.
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImageValidate()")

        self.endpoints = ApiEndpoints()

        self.path = self.endpoints.image_validate.get("path")
        self.verb = self.endpoints.image_validate.get("verb")
        self.payload = {}
        self.serial_numbers_done: Set[str] = set()

        self._init_properties()
        self.issu_detail = SwitchIssuDetailsBySerialNumber(self.module)

    def _init_properties(self) -> None:
        self.method_name = inspect.stack()[0][3]

        # self.properties is already initialized in the parent class
        self.properties["check_interval"] = 10  # seconds
        self.properties["check_timeout"] = 1800  # seconds
        self.properties["response_data"] = {}
        self.properties["result"] = {}
        self.properties["response"] = {}
        self.properties["non_disruptive"] = False
        self.properties["serial_numbers"] = None

    def prune_serial_numbers(self) -> None:
        """
        If the image is already validated on a switch, remove that switch's
        serial number from the list of serial numbers to validate.
        """
        self.method_name = inspect.stack()[0][3]

        self.issu_detail.refresh()
        serial_numbers = copy.copy(self.serial_numbers)
        for serial_number in serial_numbers:
            self.issu_detail.filter = serial_number
            if self.issu_detail.validated == "Success":
                self.serial_numbers.remove(self.issu_detail.serial_number)

    def validate_serial_numbers(self) -> None:
        """
        Log a warning if the validated state for any serial_number
        is Failed.

        TODO:1  Need a way to compare current image_policy with the image
                policy in the response
        TODO:3  If validate == Failed, it may have been from the last operation.
        TODO:3  We can't fail here based on this until we can verify the failure
                is happening for the current image_policy.
        TODO:3  Change this to a log message and update the unit test if we can't
                verify the failure is happening for the current image_policy.
        """
        self.method_name = inspect.stack()[0][3]

        for serial_number in self.serial_numbers:
            self.issu_detail.filter = serial_number
            self.issu_detail.refresh()
            if self.issu_detail.validated == "Failed":
                msg = f"{self.class_name}.{self.method_name}: "
                msg += "image validation is failing for the following switch: "
                msg += f"{self.issu_detail.device_name}, "
                msg += f"{self.issu_detail.ip_address}, "
                msg += f"{self.issu_detail.serial_number}. "
                msg += "If this persists, check the switch connectivity to "
                msg += "the controller and try again."
                self.module.fail_json(msg, **self.failed_result)

    def build_payload(self) -> None:
        """
        Build the payload for the image validation request
        """
        self.method_name = inspect.stack()[0][3]

        self.payload = {}
        self.payload["serialNum"] = self.serial_numbers
        self.payload["nonDisruptive"] = self.non_disruptive

    def commit(self) -> None:
        """
        Commit the image validation request to the controller and wait
        for the images to be validated.
        """
        self.method_name = inspect.stack()[0][3]

        if self.serial_numbers is None:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "call instance.serial_numbers before "
            msg += "calling commit."
            self.module.fail_json(msg, **self.failed_result)

        if len(self.serial_numbers) == 0:
            return

        self.prune_serial_numbers()
        self.validate_serial_numbers()
        self._wait_for_current_actions_to_complete()

        self.build_payload()
        self.properties["response"] = dcnm_send(
            self.module, self.verb, self.path, data=json.dumps(self.payload)
        )
        self.properties["result"] = self._handle_response(self.response, self.verb)

        msg = f"payload: {self.payload}"
        self.log.debug(msg)
        msg = f"response: {self.response}"
        self.log.debug(msg)
        msg = f"result: {self.result}"
        self.log.debug(msg)

        if not self.result["success"]:
            msg = f"{self.class_name}.{self.method_name}: "
            msg = f"failed: {self.result}. "
            msg += f"Controller response: {self.response}"
            self.module.fail_json(msg, **self.failed_result)

        self.properties["response_data"] = self.response
        self._wait_for_image_validate_to_complete()

    def _wait_for_current_actions_to_complete(self) -> None:
        """
        The controller will not validate an image if there are any actions in
        progress.  Wait for all actions to complete before validating image.
        Actions include image staging, image upgrade, and image validation.
        """
        self.method_name = inspect.stack()[0][3]

        self.serial_numbers_done: Set[str] = set()
        serial_numbers_todo = set(copy.copy(self.serial_numbers))
        timeout = self.check_timeout

        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
            sleep(self.check_interval)
            timeout -= self.check_interval

            for serial_number in self.serial_numbers:
                if serial_number in self.serial_numbers_done:
                    continue

                self.issu_detail.filter = serial_number
                self.issu_detail.refresh()

                if self.issu_detail.actions_in_progress is False:
                    self.serial_numbers_done.add(serial_number)

        if self.serial_numbers_done != serial_numbers_todo:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "Timed out waiting for actions to complete. "
            msg += "serial_numbers_done: "
            msg += f"{','.join(sorted(self.serial_numbers_done))}, "
            msg += "serial_numbers_todo: "
            msg += f"{','.join(sorted(serial_numbers_todo))}"
            self.module.fail_json(msg, **self.failed_result)

    def _wait_for_image_validate_to_complete(self) -> None:
        """
        Wait for image validation to complete
        """
        self.method_name = inspect.stack()[0][3]

        self.serial_numbers_done = set()
        timeout = self.check_timeout
        serial_numbers_todo = set(copy.copy(self.serial_numbers))

        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
            sleep(self.check_interval)
            timeout -= self.check_interval

            for serial_number in self.serial_numbers:
                if serial_number in self.serial_numbers_done:
                    continue

                self.issu_detail.filter = serial_number
                self.issu_detail.refresh()

                ip_address = self.issu_detail.ip_address
                device_name = self.issu_detail.device_name
                validated_percent = self.issu_detail.validated_percent
                validated_status = self.issu_detail.validated

                if validated_status == "Failed":
                    msg = f"{self.class_name}.{self.method_name}: "
                    msg = f"Seconds remaining {timeout}: validate image "
                    msg += f"{validated_status} for "
                    msg += f"{device_name}, {ip_address}, {serial_number}, "
                    msg += f"image validated percent: {validated_percent}. "
                    msg += "Check the switch e.g. show install log detail, "
                    msg += "show incompatibility-all nxos <image>.  Or "
                    msg += "check Operations > Image Management > "
                    msg += "Devices > View Details > Validate on the "
                    msg += "controller GUI for more details."
                    self.module.fail_json(msg, **self.failed_result)

                if validated_status == "Success":
                    self.serial_numbers_done.add(serial_number)
                msg = f"seconds remaining {timeout}"
                self.log.debug(msg)
                msg = f"serial_numbers_todo: {serial_numbers_todo}"
                self.log.debug(msg)
                msg = f"serial_numbers_done: {self.serial_numbers_done}"
                self.log.debug(msg)

        if self.serial_numbers_done != serial_numbers_todo:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "Timed out waiting for image validation to complete. "
            msg += "serial_numbers_done: "
            msg += f"{','.join(sorted(self.serial_numbers_done))}, "
            msg += "serial_numbers_todo: "
            msg += f"{','.join(sorted(serial_numbers_todo))}"
            self.module.fail_json(msg, **self.failed_result)

    @property
    def serial_numbers(self) -> List[str]:
        """
        Set the serial numbers of the switches to stage.

        This must be set before calling instance.commit()
        """
        return self.properties.get("serial_numbers", [])

    @serial_numbers.setter
    def serial_numbers(self, value: List[str]):
        self.method_name = inspect.stack()[0][3]

        if not isinstance(value, list):
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "instance.serial_numbers must be a "
            msg += "python list of switch serial numbers. "
            msg += f"Got {value}."
            self.module.fail_json(msg, **self.failed_result)

        self.properties["serial_numbers"] = value

    @property
    def non_disruptive(self):
        """
        Set the non_disruptive flag to True or False.
        """
        return self.properties.get("non_disruptive")

    @non_disruptive.setter
    def non_disruptive(self, value):
        self.method_name = inspect.stack()[0][3]

        value = self.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "instance.non_disruptive must be a boolean. "
            msg += f"Got {value}."
            self.module.fail_json(msg, **self.failed_result)

        self.properties["non_disruptive"] = value

    @property
    def response_data(self):
        """
        Return the result of the image staging request
        for serial_numbers.

        instance.serial_numbers must be set first.
        """
        return self.properties.get("response_data")

    @property
    def result(self):
        """
        Return the POST result
        """
        return self.properties.get("result")

    @property
    def response(self):
        """
        Return the POST response from the controller
        """
        return self.properties.get("response")

    @property
    def check_interval(self):
        """
        Return the validate check interval in seconds
        """
        return self.properties.get("check_interval")

    @check_interval.setter
    def check_interval(self, value):
        self.method_name = inspect.stack()[0][3]

        result = True
        # isinstance(True, int) is True so we need to check for bool first
        if isinstance(value, bool):
            result = False
        if not isinstance(value, int):
            result = False
        if result is False:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "instance.check_interval must be an integer. "
            msg += f"Got {value}."
            self.module.fail_json(msg, **self.failed_result)

        self.properties["check_interval"] = value

    @property
    def check_timeout(self):
        """
        Return the validate check timeout in seconds
        """
        return self.properties.get("check_timeout")

    @check_timeout.setter
    def check_timeout(self, value):
        self.method_name = inspect.stack()[0][3]

        result = True
        # isinstance(True, int) is True so we need to check for bool first
        if isinstance(value, bool):
            result = False
        if not isinstance(value, int):
            result = False
        if result is False:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "instance.check_timeout must be an integer. "
            msg += f"Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["check_timeout"] = value
