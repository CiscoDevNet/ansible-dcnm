#
# Copyright (c) 2024-2025 Cisco and/or its affiliates.
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
# pylint: disable=too-many-instance-attributes
"""
Retrieve fabric summary information from the controller.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging
from typing import Any, Literal

from ..common.api.v1.lan_fabric.rest.control.switches.switches import EpFabricSummary
from ..common.conversion import ConversionUtils
from ..common.exceptions import ControllerResponseError
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results


class FabricSummary:
    """
    # Summary

    Populate dict `self.data` with fabric summary information.

    Convenience properties are provided to access the data, including:

    - @device_count
    - @leaf_count
    - @spine_count
    - @border_gateway_count
    - @in_sync_count
    - @out_of_sync_count
    - @fabric_is_empty

    After a successful call to `refresh()`, `self.data` will contain the following structure.

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

    ## Usage

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
    fabric_is_empty = instance.fabric_is_empty
    ```
    etc...
    """

    def __init__(self):
        self.class_name: str = self.__class__.__name__

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        self.data: dict[str, dict[str, Any]] = {}
        self._conversion: ConversionUtils = ConversionUtils()
        self._ep_fabric_summary: EpFabricSummary = EpFabricSummary()
        self._results: Results = Results()
        self._rest_send: RestSend = RestSend(params={})

        # set to True in refresh() after a successful request to the controller
        # Used by getter properties to ensure refresh() has been called prior
        # to returning data.
        self.refreshed: bool = False

        self._border_gateway_count: int = 0
        self._device_count: int = 0
        self._fabric_name: str = ""
        self._leaf_count: int = 0
        self._spine_count: int = 0

        msg = "ENTERED FabricSummary()"
        self.log.debug(msg)

    def _update_device_counts(self):
        """
        # Summary

        From the controller response, update class properties pertaining to device counts.

        ## Raises

        ### ValueError

        - `self.data` is empty.
        """
        method_name: str = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg = f"self.data: {json.dumps(self.data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.data:
            msg = f"{self.class_name}.{method_name}: "
            msg += "self.data is empty. Unable to update device counts."
            raise ValueError(msg)

        self._border_gateway_count = self.data.get("switchRoles", {}).get("border gateway", 0)
        self._leaf_count = self.data.get("switchRoles", {}).get("leaf", 0)
        self._spine_count = self.data.get("switchRoles", {}).get("spine", 0)
        self._device_count = self.leaf_count + self.spine_count + self.border_gateway_count

    def _set_fabric_summary_endpoint(self) -> None:
        """
        # Summary

        Set the fabric_summary endpoint.

        ## Raises

        ### ValueError

        - Unable to retrieve the endpoint.
        """
        try:
            self._ep_fabric_summary.fabric_name = self.fabric_name
            self.rest_send.path = self._ep_fabric_summary.path
            self.rest_send.verb = self._ep_fabric_summary.verb
        except ValueError as error:
            msg = "Error retrieving fabric_summary endpoint. "
            msg += f"Detail: {error}"
            self.log.debug(msg)
            raise ValueError(msg) from error

    def _verify_controller_response(self) -> None:
        """
        # Summary

        Verify the controller response after a refresh().

        ## Raises

        ### ControllerResponseError

        -  RETURN_CODE != 200.
        -  DATA is missing or empty.
        """
        method_name: str = inspect.stack()[0][3]

        controller_return_code = self._rest_send.response_current.get("RETURN_CODE", None)
        controller_message = self._rest_send.response_current.get("MESSAGE", None)
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
        if not self.data:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Controller responded with missing or empty DATA."
            raise ControllerResponseError(msg)

    def refresh(self) -> None:
        """
        # Summary

        Refresh fabric summary info from the controller and populate `self.data` with the result.

        `self.data` is a dict of fabric summary info for one fabric.

        # Raises

        ## `ValueError` if

        - `fabric_name` is not set.
        - `rest_send` is not properly configured (rest_send.params is empty).
        - Unable to retrieve fabric_summary endpoint.
        - `_update_device_counts()` fails.

        ## `ControllerResponseError` if

        - The controller `RETURN_CODE` != 200
        """
        method_name: str = inspect.stack()[0][3]
        if self.fabric_name == "":
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Set {self.class_name}.fabric_name prior to calling "
            msg += f"{self.class_name}.refresh()."
            raise ValueError(msg)

        if self._rest_send.params == {}:
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
        save_check_mode = self._rest_send.check_mode
        self._rest_send.check_mode = False
        self._rest_send.commit()
        self._rest_send.check_mode = save_check_mode
        self.data = copy.deepcopy(self._rest_send.response_current.get("DATA", {}))
        msg = f"self.data: {json.dumps(self.data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.results.response_current = self._rest_send.response_current
        # self.results.add_response(self._rest_send.response_current)
        self.results.result_current = self._rest_send.result_current
        # self.results.add_result(self._rest_send.result_current)
        self.results.register_task_result()

        try:
            self._verify_controller_response()
        except ControllerResponseError as error:
            raise ControllerResponseError(error) from error

        # self.refreshed must be True before calling
        # self._update_device_counts() below
        self.refreshed = True
        self._update_device_counts()

    def verify_refresh_has_been_called(self, attempted_method_name: str) -> None:
        """
        # Summary

        Verify that `refresh()` has been called prior to accessing properties that depend on `refresh()`.

        # Raises

        ## ValueError

        - `refresh()` has not been called.
        """
        if self.refreshed is True:
            return
        msg = f"{self.class_name}.refresh() must be called before accessing "
        msg += f"{self.class_name}.{attempted_method_name}."
        raise ValueError(msg)

    @property
    def all_data(self) -> dict[str, dict[str, Any]]:
        """
        # Summary

        Return raw fabric summary data from the controller.

        ## Raises

        ### ValueError

        - `refresh()` has not been called.
        """
        method_name: str = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        if self.data == {}:
            msg = f"{self.class_name}.{method_name}: "
            msg += "self.data is empty. Unable to return fabric summary data. "
            msg += f"Ensure {self.class_name}.refresh() has been called successfully."
            self.log.error(msg)
            raise ValueError(msg)
        return self.data

    @property
    def border_gateway_count(self) -> int:
        """
        # Summary

        Return the number of border gateway devices in fabric fabric_name.

        ## Raises

        ### ValueError

        - `refresh()` has not been called.
        """
        method_name: str = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self._border_gateway_count

    @property
    def device_count(self) -> int:
        """
        # Summary

        Return the total number of devices in fabric fabric_name.

        ## Raises

        ### ValueError

        - `refresh()` has not been called.
        """
        method_name: str = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self._device_count

    @property
    def fabric_is_empty(self) -> bool:
        """
        # Summary

        Return True if the fabric is empty.

        ## Raises

        ### ValueError

        - `refresh()` has not been called.
        """
        method_name: str = inspect.stack()[0][3]
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
        # Summary

        -   getter: Return the fabric_name to query.
        -   setter: Set the fabric_name to query.

        ## Raises

        ### ValueError

        -   setter: fabric_name is not a string.
        -   setter: fabric_name is invalid (i.e. the controller would return an error due to invalid characters).
        """
        return self._fabric_name

    @fabric_name.setter
    def fabric_name(self, value: str):
        try:
            self._conversion.validate_fabric_name(value)
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error
        self._fabric_name = value

    @property
    def leaf_count(self) -> int:
        """
        # Summary

        Return the number of leaf devices in fabric fabric_name.

        ## Raises

        ### ValueError

        - `refresh()` has not been called.
        """
        method_name: str = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self._leaf_count

    @property
    def rest_send(self) -> RestSend:
        """
        # Summary

        An instance of the RestSend class.

        ## Raises

        -   setter: `TypeError` if the value is not an instance of RestSend.
        -   setter: `ValueError` if RestSend.params is not set.

        ## getter

        Return an instance of the RestSend class.

        ## setter

        Set an instance of the RestSend class.
        """
        method_name: str = inspect.stack()[0][3]
        if not self._rest_send.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += "RestSend.params must be set before accessing."
            raise ValueError(msg)
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        method_name: str = inspect.stack()[0][3]
        _class_have: str = ""
        _class_need: Literal["RestSend"] = "RestSend"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        # Summary

        An instance of the Results class.

        ## Raises

        -   setter: `TypeError` if the value is not an instance of Results.

        ## getter

        Return an instance of the Results class.

        ## setter

        Set an instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        method_name: str = inspect.stack()[0][3]
        _class_have: str = ""
        _class_need: Literal["Results"] = "Results"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._results = value

    @property
    def spine_count(self) -> int:
        """
        # Summary

        Return the number of spine devices in fabric fabric_name.

        ## Raises

        ### ValueError

        - `refresh()` has not been called.
        """
        method_name: str = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self._spine_count
