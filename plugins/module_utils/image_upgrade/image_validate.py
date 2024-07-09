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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.stagingmanagement.stagingmanagement import \
    EpImageValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.switch_issu_details import \
    SwitchIssuDetailsBySerialNumber


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
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    results = Results()

    instance = ImageValidate()
    # mandatory parameters
    instance.rest_send = rest_send
    instance.results = results
    instance.serial_numbers = ["FDO211218HH", "FDO211218GC"]
    # optional parameters
    instance.non_disruptive = True
    instance.commit()
    data = instance.response_data
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
        self.action = "image_validate"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.endpoint = EpImageValidate()
        self.issu_detail = SwitchIssuDetailsBySerialNumber()
        self.payload = {}
        self.serial_numbers_done: set = set()

        self._rest_send = None
        self._results = None
        self._serial_numbers = None
        self._non_disruptive = False
        self._check_interval = 10  # seconds
        self._check_timeout = 1800  # seconds

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

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
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
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
                raise ValueError(msg)

    def build_payload(self) -> None:
        """
        Build the payload for the image validation request
        """
        method_name = inspect.stack()[0][3]
        msg = f"ZZZZZ: ENTERED {self.class_name}.{method_name}: "
        msg += f"self.serial_numbers: {self.serial_numbers}"
        self.log.debug(msg)

        self.payload = {}
        self.payload["serialNum"] = self.serial_numbers
        self.payload["nonDisruptive"] = self.non_disruptive

    def register_unchanged_result(self, msg):
        """
        ### Summary
        Register a successful unchanged result with the results object.
        """
        self.results.action = self.action
        self.results.diff_current = {}
        self.results.response_current = {"response": msg}
        self.results.result_current = {"success": True, "changed": False}
        self.results.response_data = {"response": msg}
        self.results.register_task_result()

    def validate_commit_parameters(self):
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
            msg = "No serial numbers to validate."
            self.register_unchanged_result(msg)
            return

        self.issu_detail.rest_send = self.rest_send
        # We don't want the results to show up in the user's result output.
        self.issu_detail.results = Results()
        self.prune_serial_numbers()
        self.validate_serial_numbers()
        self._wait_for_current_actions_to_complete()

        self.build_payload()
        self.rest_send.verb = self.endpoint.verb
        self.rest_send.path = self.endpoint.path
        self.rest_send.payload = self.payload
        self.rest_send.commit()

        msg = "self.payload: "
        msg += f"{json.dumps(self.payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"response_current: {self.rest_send.response_current}"
        self.log.debug(msg)

        msg = f"result_current: {self.rest_send.result_current}"
        self.log.debug(msg)

        msg = f"self.response_data: {self.response_data}"
        self.log.debug(msg)

        if not self.rest_send.result_current["success"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"failed: {self.result_current}. "
            msg += f"Controller response: {self.rest_send.response_current}"
            self.results.register_task_result()
            raise ControllerResponseError(msg)

        self._wait_for_image_validate_to_complete()

        for serial_number in self.serial_numbers_done:
            self.issu_detail.filter = serial_number
            diff = {}
            diff["action"] = "validate"
            diff["ip_address"] = self.issu_detail.ip_address
            diff["logical_name"] = self.issu_detail.device_name
            diff["policy"] = self.issu_detail.policy
            diff["serial_number"] = serial_number
            # See image_upgrade_common.py for the definition of self.diff
            self.diff = copy.deepcopy(diff)
        msg = f"self.diff: {json.dumps(self.diff, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _wait_for_current_actions_to_complete(self) -> None:
        """
        ### Summary
        The controller will not validate an image if there are any actions in
        progress.  Wait for all actions to complete before validating image.
        Actions include image staging, image upgrade, and image validation.

        ### Raises
        -   ``ValueError`` if:
                -   The actions do not complete within the timeout.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        if self.rest_send.unit_test is False:
            self.serial_numbers_done: set = set()
        serial_numbers_todo = set(copy.copy(self.serial_numbers))
        timeout = self.check_timeout

        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
            if self.rest_send.unit_test is False:
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
        serial_numbers_todo = set(copy.copy(self.serial_numbers))

        msg = f"ZZZZ: {self.class_name}.{method_name}: "
        msg += f"rest_send.unit_test: {self.rest_send.unit_test}"
        msg += f"serial_numbers_todo: {sorted(serial_numbers_todo)}"
        self.log.debug(msg)

        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
            if self.rest_send.unit_test is False:
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
                msg = f"serial_numbers_todo: {sorted(serial_numbers_todo)}"
                self.log.debug(msg)
                msg = f"serial_numbers_done: {sorted(self.serial_numbers_done)}"
                self.log.debug(msg)

        if self.serial_numbers_done != serial_numbers_todo:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Timed out waiting for image validation to complete. "
            msg += "serial_numbers_done: "
            msg += f"{','.join(sorted(self.serial_numbers_done))}, "
            msg += "serial_numbers_todo: "
            msg += f"{','.join(sorted(serial_numbers_todo))}"
            raise ValueError(msg)

    @property
    def response_data(self):
        """
        ### Summary
        Return the DATA key of the controller response.
        Obtained from self.rest_send.response_current.

        commit must be called before accessing this property.
        """
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
    def serial_numbers(self, value: list):
        method_name = inspect.stack()[0][3]

        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "serial_numbers must be a python list of "
            msg += "switch serial numbers. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self._serial_numbers = value

    @property
    def non_disruptive(self):
        """
        ### Summary
        Set the non_disruptive flag to True or False.

        ### Raises
        -   ``TypeError`` if the value is not a boolean.
        """
        return self._non_disruptive

    @non_disruptive.setter
    def non_disruptive(self, value):
        method_name = inspect.stack()[0][3]

        value = self.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.non_disruptive must be a boolean. "
            msg += f"Got {value}."
            raise TypeError(msg)

        self._non_disruptive = value

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
