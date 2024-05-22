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
from typing import Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import (
    EpMaintenanceModeDisable, EpMaintenanceModeEnable)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils


class MaintenanceMode:
    """
    # Modify the maintenance mode state of a switch.

    -   Raise ``ValueError`` for any caller errors, e.g. required properties
        not being set before calling FabricConfigDeploy().commit().
    -   Update MaintenanceMode().results to reflect success/failure of
        the operation on the controller.

    ## Usage (where params is AnsibleModule.params)

    ```python
    instance = MaintenanceMode(params)
    instance.fabric_name = "MyFabric"
    instance.mode = "maintenance" # or "normal"
    instance.ip_address = "192.168.1.2"
    instance.rest_send = RestSend(ansible_module)
    instance.results = Results()
    instance.serial_number = "FDO1234567"
    try:
        instance.commit()
    except ValueError as error:
        raise ValueError(error) from error
    ```
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.params = params
        self.action = "maintenance_mode"
        self.cannot_perform_action_reason = ""
        self.action_failed = False
        self.fabric_can_be_deployed = False

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.__init__(): "
            msg += "params is missing mandatory check_mode parameter."
            raise ValueError(msg)

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.__init__(): "
            msg += "params is missing mandatory state parameter."
            raise ValueError(msg)

        self.action_result: Dict[str, bool] = {}

        self.valid_modes = ["maintenance", "normal"]
        self.path = None
        self.verb = None
        self._init_properties()

        self.conversion = ConversionUtils()
        self.ep_maintenance_mode_enable = EpMaintenanceModeEnable()
        self.ep_maintenance_mode_disable = EpMaintenanceModeDisable()

        msg = "ENTERED MaintenanceMode(): "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

    def _init_properties(self):
        self._properties = {}
        self._properties["fabric_name"] = None
        self._properties["ip_address"] = None
        self._properties["mode"] = None
        self._properties["rest_send"] = None
        self._properties["results"] = None
        self._properties["serial_number"] = None

    # def _can_fabric_be_deployed(self) -> None:
    #     """
    #     -   Set self.fabric_can_be_deployed to True if the fabric configuration
    #         can be deployed.
    #     -   Set self.fabric_can_be_deployed to False otherwise.
    #     """
    #     method_name = inspect.stack()[0][3]

    #     self.fabric_can_be_deployed = False

    #     deploy = self.payload.get("DEPLOY", None)
    #     if deploy is False or deploy is None:
    #         msg = f"Fabric {self.fabric_name} DEPLOY is False or None. "
    #         msg += "Skipping config-deploy."
    #         self.log.debug(msg)
    #         self.cannot_perform_action_reason = msg
    #         self.fabric_can_be_deployed = False
    #         self.action_failed = False
    #         return

    #     try:
    #         self.fabric_summary.fabric_name = self.fabric_name
    #     except ValueError as error:
    #         msg = f"Fabric {self.fabric_name} is invalid. "
    #         msg += "Cannot deploy fabric. "
    #         msg += f"Error detail: {error}"
    #         self.log.debug(msg)
    #         self.cannot_perform_action_reason = msg
    #         self.fabric_can_be_deployed = False
    #         self.action_failed = True
    #         return

    #     try:
    #         self.fabric_summary.refresh()
    #     except (ControllerResponseError, ValueError) as error:
    #         msg = f"{self.class_name}.{method_name}: "
    #         msg += "Error during FabricSummary().refresh(). "
    #         msg += f"Error detail: {error}"
    #         self.cannot_perform_action_reason = msg
    #         self.fabric_can_be_deployed = False
    #         self.action_failed = True
    #         return

    #     if self.fabric_summary.fabric_is_empty is True:
    #         msg = f"Fabric {self.fabric_name} is empty. "
    #         msg += "Cannot deploy an empty fabric."
    #         self.log.debug(msg)
    #         self.cannot_perform_action_reason = msg
    #         self.fabric_can_be_deployed = False
    #         self.action_failed = False
    #         return

    #     try:
    #         self.fabric_details.refresh()
    #     except ValueError as error:
    #         msg = f"{self.class_name}.{method_name}: "
    #         msg += "Error during FabricDetailsByName().refresh(). "
    #         msg += f"Error detail: {error}"
    #         self.cannot_perform_action_reason = msg
    #         self.fabric_can_be_deployed = False
    #         self.action_failed = True
    #         return

    #     self.fabric_details.filter = self.fabric_name

    #     if self.fabric_details.deployment_freeze is True:
    #         msg = f"Fabric {self.fabric_name} DEPLOYMENT_FREEZE == True. "
    #         msg += "Cannot deploy a fabric with deployment freeze enabled."
    #         self.log.debug(msg)
    #         self.cannot_perform_action_reason = msg
    #         self.fabric_can_be_deployed = False
    #         self.action_failed = False
    #         return

    #     if self.fabric_details.is_read_only is True:
    #         msg = f"Fabric {self.fabric_name} IS_READ_ONLY == True. "
    #         msg += "Cannot deploy a read only fabric."
    #         self.log.debug(msg)
    #         self.cannot_perform_action_reason = msg
    #         self.fabric_can_be_deployed = False
    #         self.action_failed = False
    #         return

    #     self.fabric_can_be_deployed = True

    def commit(self):
        """
        -   Initiate a config-deploy operation on the controller.
        -   Raise ``ValueError`` if FabricConfigDeploy().fabric_name is not set.
        -   Raise ``ValueError`` if FabricConfigDeploy().ip_address is not set.
        -   Raise ``ValueError`` if FabricConfigDeploy().mode is not set.
        -   Raise ``ValueError`` if FabricConfigDeploy().rest_send is not set.
        -   Raise ``ValueError`` if FabricConfigDeploy().results is not set.
        -   Raise ``ValueError`` if FabricConfigDeploy().serial_number is not set.
        -   Raise ``ValueError`` if the endpoint assignment fails.
        """
        method_name = inspect.stack()[0][3]

        if self.fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.fabric_name must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if self.ip_address is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.ip_address must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if self.mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.mode must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.results must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if self.serial_number is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.serial_number must be set "
            msg += "before calling commit."
            raise ValueError(msg)

        # self._can_fabric_be_deployed()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"action_failed: {self.action_failed}"
        msg += f"fabric_name: {self.fabric_name}, "
        msg += f"mode: {self.mode}, "
        msg += f"ip_address: {self.ip_address}, "
        # msg += f"fabric_can_be_deployed: {self.fabric_can_be_deployed}, "
        # msg += f"cannot_perform_action_reason: {self.cannot_perform_action_reason}"
        msg += f"serial_number: {self.serial_number}, "
        self.log.debug(msg)

        # if self.fabric_can_be_deployed is False:
        #     self.results.diff_current = {}
        #     self.results.action = self.action
        #     self.results.check_mode = self.check_mode
        #     self.results.state = self.state
        #     self.results.response_current = {
        #         "RETURN_CODE": 200,
        #         "MESSAGE": self.cannot_perform_action_reason,
        #     }
        #     if self.action_failed is True:
        #         self.results.result_current = {"changed": False, "success": False}
        #     else:
        #         self.results.result_current = {"changed": True, "success": True}
        #     self.results.register_task_result()
        #     return

        if self.mode == "maintenance":
            endpoint = self.ep_maintenance_mode_enable
        else:
            endpoint = self.ep_maintenance_mode_disable

        try:
            endpoint.fabric_name = self.fabric_name
            endpoint.serial_number = self.serial_number
            self.path = endpoint.path
            self.verb = endpoint.verb
        except ValueError as error:
            self.results.diff_current = {}
            self.results.result_current = self.results.failed_result
            self.results.register_task_result()
            raise ValueError(error) from error

        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.payload = None
        self.rest_send.commit()

        result = self.rest_send.result_current["success"]
        self.action_result[self.ip_address] = result
        if self.action_result[self.ip_address] is False:
            self.results.diff_current = {}
        else:
            self.results.diff_current = {
                "ip_address": self.ip_address,
                f"{self.action}": "OK",
            }

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state
        self.results.response_current = copy.deepcopy(self.rest_send.response_current)
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.register_task_result()

    @property
    def fabric_name(self):
        """
        The name of the fabric to config-save.
        """
        return self._properties["fabric_name"]

    @fabric_name.setter
    def fabric_name(self, value):
        try:
            self.conversion.validate_fabric_name(value)
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error
        self._properties["fabric_name"] = value

    @property
    def ip_address(self):
        """
        -   The ip_address of the switch.  Used only for more informative
            error messages.
        -   Raise ``ValueError`` if the value is not a string.
        """
        return self._properties["ip_address"]

    @ip_address.setter
    def ip_address(self, value):
        method_name = inspect.stack()[0][3]

        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name} must be a string. "
            msg += f"Got type: {type(value).__name__}."
            self.log.debug(msg)
            raise ValueError(msg)
        self._properties["ip_address"] = value

    @property
    def mode(self):
        """
        The indended mode.
        -   getter: Return the mode.
        -   setter: Set the mode.
        -   setter: Raise ``ValueError`` if the value is not one of
            "maintenance" or "normal".
        """
        return self._properties["mode"]

    @mode.setter
    def mode(self, value):
        if value not in self.valid_modes:
            msg = f"{self.class_name}.mode is invalid. "
            msg += f"Got value {value}. "
            msg += f"Expected one of {','.join(self.valid_modes)}."
            raise ValueError(msg)
        self._properties["mode"] = value

    @property
    def rest_send(self):
        """
        -   getter: Return an instance of the RestSend class.
        -   setter: Set an instance of the RestSend class.
        -   setter: Raise ``TypeError`` if the value is not an
            instance of RestSend.
        """
        return self._properties["rest_send"]

    @rest_send.setter
    def rest_send(self, value):
        method_name = inspect.stack()[0][3]
        _class_name = None
        msg = f"{self.class_name}.{method_name}: "
        msg += "value must be an instance of RestSend. "
        try:
            _class_name = value.class_name
        except AttributeError as error:
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        if _class_name != "RestSend":
            self.log.debug(msg)
            raise TypeError(msg)
        self._properties["rest_send"] = value

    @property
    def results(self):
        """
        -   getter: Return an instance of the Results class.
        -   setter: Set an instance of the Results class.
        -   setter: Raise ``TypeError`` if the value is not an
            instance of Results.
        """
        return self._properties["results"]

    @results.setter
    def results(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "value must be an instance of Results. "
        msg += f"Got value {value} of type {type(value).__name__}."
        _class_name = None
        try:
            _class_name = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            self.log.debug(msg)
            raise TypeError(msg) from error
        if _class_name != "Results":
            self.log.debug(msg)
            raise TypeError(msg)
        self._properties["results"] = value

    @property
    def serial_number(self):
        """
        -   The serial_number of the switch.
        -   Raise ``ValueError`` if the value is not a string.
        """
        return self._properties["serial_number"]

    @serial_number.setter
    def serial_number(self, value):
        method_name = inspect.stack()[0][3]

        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name} must be a string. "
            msg += f"Got type: {type(value).__name__}."
            self.log.debug(msg)
            raise ValueError(msg)
        self._properties["serial_number"] = value
