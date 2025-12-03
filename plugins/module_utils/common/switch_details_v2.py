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
"""
Retrieve switch details from the controller and provide property accessors for the switch attributes.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import inspect
import logging
from typing import Any, Literal

from .api.v1.lan_fabric.rest.inventory.inventory import EpAllSwitches
from .conversion import ConversionUtils
from .exceptions import ControllerResponseError
from .operation_type import OperationType
from .rest_send_v2 import RestSend
from .results_v2 import Results


class SwitchDetails:
    """
    # Summary

    Retrieve switch details from the controller and provide property accessors
    for the switch attributes.

    ## Raises

    ### ControllerResponseError

    -   The controller RETURN_CODE is not 200.

    ### ValueError

    -   Mandatory parameters are not set.
    -   There was an error configuring `RestSend()` e.g. invalid property values, etc.

    ## Usage

    - Where `ansible_module` is an instance of `AnsibleModule`

    ```python
    # params could also be set to ansible_module.params
    params = {"state": "merged", "check_mode": False}
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(params)
    rest_send.sender = sender
    try:
        instance = SwitchDetails()
        instance.results = Results()
        instance.rest_send = rest_send
        instance.refresh()
    except (ControllerResponseError, ValueError) as error:
        # Handle error
    instance.filter = "10.1.1.1"
    fabric_name = instance.fabric_name
    serial_number = instance.serial_number
    etc...
    ```

    """

    def __init__(self) -> None:
        self.class_name: str = self.__class__.__name__

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        self.action: str = "switch_details"
        self._conversion: ConversionUtils = ConversionUtils()
        self._ep_all_switches: EpAllSwitches = EpAllSwitches()
        self._filter: str = ""
        self._info: dict[str, Any] = {}
        self._rest_send: RestSend = RestSend({})
        self._results = Results()
        self._results.action = self.action
        self._results.operation_type = OperationType.QUERY

        msg = f"{self.class_name}.__init__ ENTERED."
        self.log.debug(msg)

    def validate_refresh_parameters(self) -> None:
        """
        # Summary

        Validate that mandatory parameters are set before calling refresh().

        ## Raises

        ### ValueError

        - instance.rest_send.params is not set.
        """
        method_name: str = inspect.stack()[0][3]
        if not self.rest_send.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set before calling "
            msg += f"{self.class_name}.refresh()."
            raise ValueError(msg)

    def send_request(self) -> None:
        """
        # Summary

        Send the request to the controller.

        ## Raises

        ### ValueError

        - The RestSend object raises `TypeError` or `ValueError`.

        """
        # Send request
        try:
            self.rest_send.save_settings()
            self.rest_send.timeout = 1
            # Regardless of ansible_module.check_mode, we need to get the
            # switch details. So, set check_mode to False.
            self.rest_send.check_mode = False
            self.rest_send.path = self._ep_all_switches.path
            self.rest_send.verb = self._ep_all_switches.verb
            self.rest_send.commit()
            self.rest_send.restore_settings()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

    def update_results(self) -> None:
        """
        # Summary

        Update and register the results.

        ## Raises

        ### ControllerResponseError

        - The controller RETURN_CODE is not 200.

        ### ValueError

        - `Results()` raises `TypeError`.
        """
        method_name: str = inspect.stack()[0][3]
        # Update and register results
        try:
            self.results.action = self.action
            self.results.response_current = self.rest_send.response_current
            self.results.result_current = self.rest_send.result_current
            # SwitchDetails never changes the controller state
            self.results.add_changed(False)

            if self.results.response_current["RETURN_CODE"] == 200:
                self.results.add_failed(False)
            else:
                self.results.add_failed(True)
            self.results.register_task_result()
        except TypeError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error updating results. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        if True in self.results.failed:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Unable to retrieve switch information from the controller. "
            msg += f"Got response {self.results.response_current}"
            raise ControllerResponseError(msg)

    def refresh(self) -> None:
        """
        # Summary

        Refresh switch_details with current switch details from the controller.

        ## Raises

        ### ValueError

        - Mandatory parameters are not set.
        - There was an error configuring RestSend() e.g. invalid property values, etc.
        - There is an error sending the request to the controller.
        - There is an error updating controller results.
        """
        method_name: str = inspect.stack()[0][3]
        try:
            self.validate_refresh_parameters()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Mandatory parameters need review. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        try:
            self.send_request()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error sending request to the controller. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        try:
            self.update_results()
        except (ControllerResponseError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error updating results. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        data: list[dict[str, Any]] = self.results.response_current.get("DATA", {})
        self._info = {}
        for switch in data:
            if switch.get("ipAddress", None) is None:
                continue
            self._info[switch["ipAddress"]] = switch

    def _get(self, item) -> Any:
        """
        # Summary

        Return the value of the item from the filtered switch.

        ## Raises

        ### ValueError

        - `filter` is not set.
        - `filter` is not in the controller response.
        - `item` is not in the filtered switch dict.
        """
        method_name: str = inspect.stack()[0][3]

        if not self._filter:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter before accessing "
            msg += f"property {item}."
            raise ValueError(msg)

        if self._filter not in self._info:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Switch with ip_address {self._filter} does not exist on "
            msg += "the controller."
            raise ValueError(msg)

        if item not in self._info[self._filter]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self._filter} does not have a key named {item}."
            raise ValueError(msg)

        return self._conversion.make_boolean(self._conversion.make_none(self._info[self._filter].get(item)))

    @property
    def filter(self) -> str:
        """
        # Summary

        Get/set the query filter.

        ## Raises

        None. However, if `filter` is not set, or `filter` is set to a non-existent switch,
        `ValueError` will be raised when accessing the various getter properties.

        ## Details

        The filter should be the ip_address of the switch from which to retrieve details.

        `filter` must be set before accessing this class's properties.
        """
        return self._filter

    @filter.setter
    def filter(self, value: str) -> None:
        self._filter = value

    @property
    def fabric_name(self) -> str:
        """
        # Summary

        The `fabricName` of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `fabricName` of the filtered switch, if it exists.
        -   Empty string otherwise.
        """
        value = self._get("fabricName")
        if value is None:
            return ""
        return value

    @property
    def freeze_mode(self) -> bool:
        """
        # Summary

        The `freezeMode` of the filtered switch's fabric.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `freezeMode` (bool) of the filtered switch's fabric, if it exists.
        - False otherwise
        """
        value = self._get("freezeMode")
        if value not in [False, True]:
            return False
        return value

    @property
    def hostname(self) -> str:
        """
        # Summary

        The `hostName` of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `hostName` of the filtered switch, if it exists.
        -   Empty string otherwise.

        ## NOTES

        - `hostname` is "" for NDFC version 12.1.2e
        - Better to use `logical_name` which is populated in both NDFC versions 12.1.2e and 12.1.3b
        """
        value = self._get("hostName")
        if value is None:
            return ""
        return value

    @property
    def info(self) -> dict[str, Any]:
        """
        # Summary

        Parsed data from the GET request.

        ## Raises

        None

        ## Returns

        - Parsed data from the GET request, if it exists.
        - An empty dictionary otherwise

        ## Notes

        - Keyed on ip_address
        """
        return self._info

    @property
    def is_non_nexus(self) -> bool:
        """
        # Summary

        The `isNonNexus` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `isNonNexus` value of the filtered switch, if it exists.
        -   False otherwise.
        """
        value = self._get("isNonNexus")
        if value not in [False, True]:
            return False
        return value

    @property
    def logical_name(self) -> str:
        """
        # Summary

        The `logicalName` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `logicalName` value of the filtered switch, if it exists.
        - Empty string otherwise.
        """
        value = self._get("logicalName")
        if value is None:
            return ""
        return value

    @property
    def maintenance_mode(self) -> str:
        """
        # Summary

        - Return a synthesized value for `maintenanceMode` status of the filtered switch, if it exists.
        - Return `mode` otherwise.

        ## Raises

        ### ValueError

        - `mode` cannot be ascertained.
        - `system_mode` cannot be ascertained.

        ## Possible values

        - `inconsistent`: `mode` and `system_mode` differ. See NOTES.
        - `maintenance`: The switch is in maintenance mode.  It has withdrawn its routes, etc,
          from the fabric so that traffic does not traverse the switch.  Maintenance operations
          will not impact traffic in the hosting fabric.
        - `migration`: The switch config is not compatible with the switch role in the hosting fabric.
          Manual remediation is required.
        - `normal`: The switch is participating as a traffic forwarding agent in the hosting fabric.

        ## Notes

        - `mode` is the current NDFC configured value of the switch's `systemMode` (`system_mode`),
          whereas `system_mode` is the current value on the switch.  When these differ, NDFC displays
          `inconsistent` for the switch's `maintenanceMode` state. To resolve `inconsistent` state, a
          switch `config-deploy` must be initiated on the controller.
        """
        method_name: str = inspect.stack()[0][3]
        if not self.mode:
            msg = f"{self.class_name}.{method_name}: "
            msg += "mode is not set. Either 'filter' has not been "
            msg += "set, or the controller response is invalid."
            raise ValueError(msg)
        if not self.system_mode:
            msg = f"{self.class_name}.{method_name}: "
            msg += "system_mode is not set. Either 'filter' has not been "
            msg += "set, or the controller response is invalid."
            raise ValueError(msg)
        if self.mode.lower() == "migration":
            return "migration"
        if self.mode.lower() != self.system_mode.lower():
            return "inconsistent"
        return self.mode

    @property
    def managable(self) -> bool:
        """
        # Summary

        The `managable` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `managable` value of the filtered switch, if it exists.
        -   False otherwise.

        ## Example Values

        - True
        - False

        ## Notes

        -   Yes, managable is misspelled.  It is spelled this way in the controller response.

        ## See also

        - `manageable` property which is a correctly-spelled alias of `managable`.
        -  Both properties return the same value.
        """
        value = self._get("managable")
        if value not in [False, True]:
            return False
        return value

    @property
    def manageable(self) -> bool:
        """
        # Summary

        The `managable` (yes, this is misspelled in the controller response) value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `managable` value of the filtered switch, if it exists.
        -   False otherwise.

        ## Example Values

        - True
        - False

        ## See also

        - `managable` property which is an incorrectly-spelled property that matches the controller response.
        -  Both properties return the same value.
        """
        value = self._get("managable")
        if value not in [False, True]:
            return False
        return value

    @property
    def mode(self) -> str:
        """
        # Summary

        The `mode` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `mode` value of the filtered switch, if it exists.
        -   An empty string otherwise.
        -   Example: maintenance, migration, normal, inconsistent, ""
        """
        value = self._get("mode")
        if value is None:
            return ""
        return value.lower()

    @property
    def model(self) -> str:
        """
        # Summary

        The `model` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `model` value of the filtered switch, if it exists.
        -   An empty string otherwise.
        """
        value = self._get("model")
        if value is None:
            return ""
        return value

    @property
    def oper_status(self) -> str:
        """
        # Summary

        The `operStatus` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `operStatus` value of the filtered switch, if it exists.
        -   "Unknown" otherwise.

        ## Example Values

        - Minor
        - Healthy
        - Unknown
        """
        value = self._get("operStatus")
        if value is None:
            return "Unknown"
        return value

    @property
    def platform(self) -> str:
        """
        # Summary

        The `platform` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `platform` value of the filtered switch, if it exists.
        -   An empty string otherwise.

        ## Example Values

        - N9K (derived from N9K-C93180YC-EX)
        - ""

        ## Notes

        - `platform` is derived from `model`. It is not in the controller response.
        """
        value = self._get("model")
        if value is None:
            return ""
        return value.split("-")[0]

    @property
    def release(self) -> str:
        """
        # Summary

        The `release` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `release` value of the filtered switch, if it exists.
        - An empty string otherwise.

        ## Example Values

        - 10.2(5)
        """
        value = self._get("release")
        if value is None:
            return ""
        return value

    @property
    def role(self) -> str:
        """
        # Summary

        The `switchRole` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `switchRole` value of the filtered switch, if it exists.
        -   An empty string otherwise.

        ## Example Values

        - leaf
        - spine

        ## Notes

        - `role` is an alias of `switch_role`.
        """
        value = self._get("switchRole")
        if value is None:
            return ""
        return value

    @property
    def serial_number(self) -> str:
        """
        # Summary

        The `serialNumber` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `serialNumber` value of the filtered switch, if it exists.
        - Empty string otherwise.
        """
        value = self._get("serialNumber")
        if value is None:
            return ""
        return value

    @property
    def source_interface(self) -> str:
        """
        # Summary

        The `sourceInterface` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `sourceInterface` value of the filtered switch, if it exists.
        - An empty string otherwise.
        """
        value = self._get("sourceInterface")
        if value is None:
            return ""
        return value

    @property
    def source_vrf(self) -> str:
        """
        # Summary

        The `sourceVrf` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `sourceVrf` value of the filtered switch, if it exists.
        - An empty string otherwise.
        """
        value = self._get("sourceVrf")
        if value is None:
            return ""
        return value

    @property
    def status(self) -> str:
        """
        # Summary

        The `status` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `status` value of the filtered switch, if it exists.
        - An empty string otherwise.
        """
        value = self._get("status")
        if value is None:
            return ""
        return value

    @property
    def switch_db_id(self) -> str:
        """
        # Summary

        The `switchDbID` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `switchDbID` value of the filtered switch, if it exists.
        - An empty string otherwise.
        """
        value = self._get("switchDbID")
        if value is None:
            return ""
        return value

    @property
    def switch_role(self) -> str:
        """
        # Summary

        The `switchRole` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `switchRole` value of the filtered switch, if it exists.
        - An empty string otherwise.
        """
        value = self._get("switchRole")
        if value is None:
            return ""
        return value

    @property
    def switch_uuid(self) -> str:
        """
        # Summary

        The `swUUID` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `swUUID` value of the filtered switch, if it exists.
        - An empty string otherwise.
        """
        value = self._get("swUUID")
        if value is None:
            return ""
        return value

    @property
    def switch_uuid_id(self) -> str:
        """
        # Summary

        The `swUUIDId` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        - The `swUUIDId` value of the filtered switch, if it exists.
        - An empty string otherwise.
        """
        value = self._get("swUUIDId")
        if value is None:
            return ""
        return value

    @property
    def system_mode(self) -> str:
        """
        # Summary

        The `systemMode` value of the filtered switch.

        ## Raises

        ### ValueError

        - See `filter` setter and `_get` method.

        ## Returns

        -   The `systemMode` value of the filtered switch, if it exists.
        -   An empty string otherwise.
        """
        value = self._get("systemMode")
        if value is None:
            return ""
        return value

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
        if not value.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += "RestSend.params must be set."
            raise ValueError(msg)
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
        self._results.action = self.action
        self._results.operation_type = OperationType.QUERY
