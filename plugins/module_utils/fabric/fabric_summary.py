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

from ..common.api.v1.lan_fabric.rest.control.switches.switches import \
    EpFabricSummary
from ..common.conversion import ConversionUtils
from ..common.exceptions import ControllerResponseError
from ..common.results import Results
from .common import FabricCommon


class FabricSummary(FabricCommon):
    """
    Populate ``dict`` ``self.data`` with fabric summary information.

    Convenience properties are provided to access the data, including:

    - @device_count
    - @leaf_count
    - @spine_count
    - @border_gateway_count
    - @in_sync_count
    - @out_of_sync_count

    self.data will contain the following structure.

    ```python
    {
        "switchSWVersions": {
            "10.2(5)": 7,
            "10.3(1)": 2
        },
        "switchHealth": {
            "Healthy": 2,
            "Minor": 7
        },
        "switchHWVersions": {
            "N9K-C93180YC-EX": 4,
            "N9K-C9504": 5
        },
        "switchConfig": {
            "Out-of-Sync": 5,
            "In-Sync": 4
        },
        "switchRoles": {
            "leaf": 4,
            "spine": 3,
            "border gateway": 2
        }
    }
    ```
    Usage:

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

    instance = FabricSummary()
    instance.rest_send = rest_send
    instance.fabric_name = "MyFabric"
    instance.refresh()
    fabric_summary = instance.data
    device_count = instance.device_count
    ```
    etc...
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.data = None
        self.ep_fabric_summary = EpFabricSummary()
        self.conversion = ConversionUtils()

        # set to True in refresh() after a successful request to the controller
        # Used by getter properties to ensure refresh() has been called prior
        # to returning data.
        self.refreshed = False

        self.results = Results()

        self._border_gateway_count = 0
        self._device_count = 0
        self._fabric_name = None
        self._leaf_count = 0
        self._spine_count = 0

        msg = "ENTERED FabricSummary()"
        self.log.debug(msg)

    def _update_device_counts(self):
        """
        -   From the controller response, update class properties
            pertaining to device counts.
        -   By the time refresh() calls this method, self.data
            has been verified, so no need to verify it here.
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg = f"self.data: {json.dumps(self.data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self._border_gateway_count = self.data.get("switchRoles", {}).get(
            "border gateway", 0
        )
        self._leaf_count = self.data.get("switchRoles", {}).get("leaf", 0)
        self._spine_count = self.data.get("switchRoles", {}).get(
            "spine", 0
        )
        self._device_count = (
            self.leaf_count + self.spine_count + self.border_gateway_count
        )

    def _set_fabric_summary_endpoint(self):
        """
        -   Set the fabric_summary endpoint.
        -   Raise ``ValueError`` if unable to retrieve the endpoint.
        """
        try:
            self.ep_fabric_summary.fabric_name = self.fabric_name
            # pylint: disable=no-member
            self.rest_send.path = self.ep_fabric_summary.path
            self.rest_send.verb = self.ep_fabric_summary.verb
        except ValueError as error:
            msg = "Error retrieving fabric_summary endpoint. "
            msg += f"Detail: {error}"
            self.log.debug(msg)
            raise ValueError(msg) from error

    def _verify_controller_response(self):
        """
        -  Raise ``ControllerResponseError`` if RETURN_CODE != 200.
        -  Raise ``ControllerResponseError`` if DATA is missing or empty.
        """
        method_name = inspect.stack()[0][3]

        # pylint: disable=no-member
        controller_return_code = self.rest_send.response_current.get(
            "RETURN_CODE", None
        )
        controller_message = self.rest_send.response_current.get("MESSAGE", None)
        if controller_return_code != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Failed to retrieve fabric_summary for fabric_name "
            msg += f"{self.fabric_name}. "
            msg += f"RETURN_CODE: {controller_return_code}. "
            msg += f"MESSAGE: {controller_message}."
            self.log.error(msg)
            raise ControllerResponseError(msg)

        # DATA is set to an empty dict in refresh() if the controller response
        # does not contain a DATA key.
        if len(self.data) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Controller responded with missing or empty DATA."
            raise ControllerResponseError(msg)

    def refresh(self):
        """
        -   Refresh fabric summary info from the controller and
            populate ``self.data`` with the result.
        -   ``self.data`` is a ``dict`` of fabric summary info for one fabric.
        -   raise ``ValueError`` if ``fabric_name`` is not set.
        -   raise ``ValueError`` if unable to retrieve fabric_summary endpoint.
        -   raise ``ValueError`` if ``_update_device_counts()`` fails.
        -   raise ``ControllerResponseError`` if the controller
            ``RETURN_CODE`` != 200
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Set {self.class_name}.fabric_name prior to calling "
            msg += f"{self.class_name}.refresh()."
            raise ValueError(msg)

        # pylint: disable=no-member
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Set {self.class_name}.rest_send prior to calling "
            msg += f"{self.class_name}.refresh()."
            raise ValueError(msg)

        try:
            self._set_fabric_summary_endpoint()
        except ValueError as error:
            raise ValueError(error) from error

        # We always want to get the controller's current fabric state,
        # regardless of the current value of check_mode.
        # We save the current check_mode value, set rest_send.check_mode
        # to False so the request will be sent to the controller, and then
        # restore the original check_mode value.
        save_check_mode = self.rest_send.check_mode
        self.rest_send.check_mode = False
        self.rest_send.commit()
        self.rest_send.check_mode = save_check_mode
        self.data = copy.deepcopy(self.rest_send.response_current.get("DATA", {}))

        msg = f"self.data: {json.dumps(self.data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.results.response_current = self.rest_send.response_current
        self.results.response = self.rest_send.response_current
        self.results.result_current = self.rest_send.result_current
        self.results.result = self.rest_send.result_current
        self.results.register_task_result()

        # pylint: enable=no-member
        try:
            self._verify_controller_response()
        except ControllerResponseError as error:
            raise ControllerResponseError(error) from error

        # self.refreshed must be True before calling
        # self._update_device_counts() below
        self.refreshed = True
        self._update_device_counts()

    def verify_refresh_has_been_called(self, attempted_method_name):
        """
        - raise ``ValueError`` if ``refresh()`` has not been called.
        """
        if self.refreshed is True:
            return
        msg = f"{self.class_name}.refresh() must be called before accessing "
        msg += f"{self.class_name}.{attempted_method_name}."
        raise ValueError(msg)

    @property
    def all_data(self) -> dict:
        """
        - Return raw fabric summary data from the controller.
        - Raise ``ValueError`` if ``refresh()`` has not been called.
        """
        method_name = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self.data

    @property
    def border_gateway_count(self) -> int:
        """
        - Return the number of border gateway devices in fabric fabric_name.
        - Raise ``ValueError`` if ``refresh()`` has not been called.
        """
        method_name = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self._border_gateway_count

    @property
    def device_count(self) -> int:
        """
        - Return the total number of devices in fabric fabric_name.
        - Raise ``ValueError`` if ``refresh()`` has not been called.
        """
        method_name = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self._device_count

    @property
    def fabric_is_empty(self) -> bool:
        """
        - Return True if the fabric is empty.
        - Raise ``ValueError`` if ``refresh()`` has not been called.
        """
        method_name = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        if self.device_count == 0:
            return True
        return False

    @property
    def fabric_name(self) -> str:
        """
        -   getter: Return the fabric_name to query.
        -   setter: Set the fabric_name to query.
        -   setter: Raise ``ValueError`` if fabric_name is not a string.
        -   setter: Raise ``ValueError`` if fabric_name is invalid (i.e.
            the controller would return an error due to invalid characters).
        """
        return self._fabric_name

    @fabric_name.setter
    def fabric_name(self, value: str):
        try:
            self.conversion.validate_fabric_name(value)
        except ValueError as error:
            raise ValueError(error) from error
        self._fabric_name = value

    @property
    def leaf_count(self) -> int:
        """
        - Return the number of leaf devices in fabric fabric_name.
        - Raise ``ValueError`` if ``refresh()`` has not been called.
        """
        method_name = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self._leaf_count

    @property
    def spine_count(self) -> int:
        """
        - Return the number of spine devices in fabric fabric_name.
        - Raise ``ValueError`` if ``refresh()`` has not been called.
        """
        method_name = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self._spine_count
