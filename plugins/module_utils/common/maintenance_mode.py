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
    EpFabricConfigDeploy, EpMaintenanceModeDisable, EpMaintenanceModeEnable)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils


class MaintenanceMode:
    """
    ### Modify the maintenance mode state of switches.

    -   Raise ``ValueError`` for any caller errors, e.g. required properties
        not being set before calling MaintenanceMode().commit().
    -   Update MaintenanceMode().results to reflect success/failure of
        the operation on the controller.
    -   For switches that are to be deployed, initiate a per-fabric
        bulk config-deploy.

    ### Example value for ``config`` in the Usage section below:
    ```json
    [
        {
            "deploy": false,
            "fabric_name": "MyFabric",
            "ip_address": "192.168.1.2",
            "mode": "maintenance",
            "serial_number": "FCI1234567"
        },
        {
            "deploy": true,
            "fabric_name": "YourFabric",
            "ip_address": "192.168.1.3",
            "mode": "normal",
            "serial_number": "HMD2345678"
        }
    ]
    ```

    ### Usage
    -   Where ``params`` is ``AnsibleModule.params``
    -   Where ``config`` is a list of dicts, each containing the following:
        -   ``deploy``: ``bool``.  If True, the switch maintenance mode
            will be deployed.
        -   ``fabric_name``: ``str``.  The name of the switch's hosting fabric.
        -   ``ip_address``: ``str``.  The ip address of the switch.
        -   ``mode``: ``str``.  The intended maintenance mode.  Must be one of
            "maintenance" or "normal".
        -   ``serial_number``: ``str``.  The serial number of the switch.



    ```python
    instance = MaintenanceMode(params)
    try:
        instance.config = config
    except ValueError as error:
        raise ValueError(error) from error
    instance.rest_send = RestSend(ansible_module)
    instance.results = Results()
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

        # Populated in build_deploy_dict()
        self.deploy_dict = {}
        # Populated in build_endpoints_list()
        self.endpoints = []
        self.action_result: Dict[str, bool] = {}
        self.serial_number_to_ip_address = {}

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
        self._properties["config"] = None
        self._properties["rest_send"] = None
        self._properties["results"] = None

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

    def verify_config_parameters(self, value):
        """
        Verify that required parameters are present in config.

        ### Raises
        -   ``ValueError`` if ``config`` is not a list.
        -   ``ValueError`` if ``config`` contains invalid content.

        ### NOTES
        1. See the following validation methods for details:
            -   verify_deploy()
            -   verify_fabric_name()
            -   verify_ip_address()
            -   verify_mode()
            -   verify_serial_number()
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.config must be a list. "
            msg += f"Got type: {type(value).__name__}."
            raise ValueError(msg)

        for item in value:
            try:
                self.verify_deploy(item)
                self.verify_fabric_name(item)
                self.verify_ip_address(item)
                self.verify_mode(item)
                self.verify_serial_number(item)
            except ValueError as error:
                raise ValueError(error) from error

    def verify_deploy(self, item):
        """
        -   Raise ``ValueError`` if ``deploy`` is not present.
        -   Raise ``ValueError`` if ``deploy`` is not a boolean.
        """
        method_name = inspect.stack()[0][3]
        if item.get("deploy", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "deploy must be present in config."
            raise ValueError(msg)
        if not isinstance(item.get("deploy", None), bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "deploy must be a boolean."
            raise ValueError(msg)

    def verify_fabric_name(self, item):
        """
        -   Raise ``ValueError`` if ``fabric_name`` is not present.
        -   Raise ``ValueError`` if ``fabric_name`` is not a valid fabric name.
        """
        method_name = inspect.stack()[0][3]
        if item.get("fabric_name", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name must be present in config."
            raise ValueError(msg)
        try:
            self.conversion.validate_fabric_name(item.get("fabric_name", None))
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

    def verify_ip_address(self, item):
        """
        -   Raise ``ValueError`` if ``ip_address`` is not present.
        """
        method_name = inspect.stack()[0][3]
        if item.get("ip_address", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "ip_address must be present in config."
            raise ValueError(msg)

    def verify_mode(self, item):
        """
        ### Summary
        Validate the ``mode`` parameter.

        ### Raises
        -   ``ValueError`` if ``mode`` is not present.
        -   ``ValueError`` if ``mode`` is not one of "maintenance" or "normal".
        """
        method_name = inspect.stack()[0][3]
        if item.get("mode", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "mode must be present in config."
            raise ValueError(msg)
        if item.get("mode", None) not in self.valid_modes:
            msg = f"{self.class_name}.{method_name}: "
            msg += "mode must be one of 'maintenance' or 'normal'."
            raise ValueError(msg)

    def verify_serial_number(self, item):
        """
        ### Summary
        Validate the ``serial_number`` parameter.

        ### Raises
        - ``ValueError`` if ``serial_number`` is not present.
        """
        method_name = inspect.stack()[0][3]
        if item.get("serial_number", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "serial_number must be present in config."
            raise ValueError(msg)

    def build_deploy_dict(self):
        """
        ### Summary
        -   Build the deploy_dict, keyed on fabric_name, with a list of
            serial_numbers to deploy for each fabric.
        """
        self.deploy_dict = {}
        for item in self.config:
            fabric_name = item.get("fabric_name")
            serial_number = item.get("serial_number")
            deploy = item.get("deploy")
            if fabric_name not in self.deploy_dict:
                self.deploy_dict[fabric_name] = []
            if deploy is True:
                self.deploy_dict[fabric_name].append(serial_number)

    def build_endpoints_list(self):
        """
        ### Summary
        -   Build the maintenance_mode endpoints to send to the controller.
            This is a list of tuples, each containing the path, verb, and
            comma-separated list of ip addresses.
            i.e. [(path, verb, ip_addresses), (path, verb, ip_addresses), ...]
        -   Also populate self.serial_number_to_ip_address dict, keyed on
            serial_number, and value of ip_address associated with
            serial_number.  This is used later in the commit() method.

        ### Raises
        -   ``ValueError`` if ``config`` is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.config is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.config must be set "
            msg += "before calling commit."
            raise ValueError(msg)

        self.serial_number_to_ip_address = {}
        # Populate dict to sort serial_numbers by fabric and mode
        # This drives endpoint creation further below.
        mode_dict = {}
        for item in self.config:
            fabric_name = item.get("fabric_name")
            serial_number = item.get("serial_number")
            mode = item.get("mode")
            ip_address = item.get("ip_address")
            self.serial_number_to_ip_address[serial_number] = ip_address
            if fabric_name not in mode_dict:
                mode_dict[fabric_name] = {}
            if mode not in mode_dict[fabric_name]:
                mode_dict[fabric_name][mode] = []
            mode_dict[fabric_name][mode].append(serial_number)

        # populate endpoints using mode_dict
        self.endpoints = []
        for fabric, data in mode_dict.items():
            for mode, serial_numbers in data.items():
                for serial_number in serial_numbers:
                    ip_address = self.serial_number_to_ip_address[serial_number]
                    if mode == "normal":
                        instance = self.ep_maintenance_mode_disable
                    else:
                        instance = self.ep_maintenance_mode_enable
                    instance.fabric_name = fabric
                    instance.serial_number = serial_number
                    endpoint = (instance.path, instance.verb, ip_address, mode)
                    self.endpoints.append(copy.copy(endpoint))

    def verify_commit_parameters(self):
        """
        ### Summary
        Verify that required parameters are present before calling commit.

        ### Raises
        -   ``ValueError`` if ``rest_send`` is not set.
        -   ``ValueError`` if ``results`` is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.config is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.config must be set "
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

    def commit(self):
        """
        ### Summary
        Initiates the maintenance mode change on the controller.

        ### Raises
        -   ``ValueError`` if ``rest_send`` is not set.
        -   ``ValueError`` if ``results`` is not set.
        """
        try:
            self.verify_commit_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        self.change_system_mode()
        self.deploy_switches()

    def change_system_mode(self):
        """
        Change the ``systemMode`` configuration for the switch.

        ### Raises
        -   ``ValueError`` if endpoint resolution fails.
        """
        self.build_endpoints_list()
        for endpoint in self.endpoints:
            self.rest_send.path = endpoint[0]
            self.rest_send.verb = endpoint[1]
            self.rest_send.payload = None
            self.rest_send.commit()

            action = "maintenance_mode"
            result = self.rest_send.result_current["success"]
            if result is False:
                self.results.diff_current = {}
            else:
                self.results.diff_current = {
                    "ip_address": endpoint[2],
                    f"{action}": endpoint[3],
                }

            self.results.action = self.action
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

    def deploy_switches(self):
        """
        Initiate config-deploy for the switches in ``self.deploy_dict``.
        """
        self.build_deploy_dict()
        ep_deploy = EpFabricConfigDeploy()
        for fabric, serial_numbers in self.deploy_dict.items():
            # Start the config-deploy
            ep_deploy.fabric_name = fabric
            ep_deploy.switch_id = serial_numbers
            self.rest_send.path = ep_deploy.path
            self.rest_send.verb = ep_deploy.verb
            self.rest_send.payload = None
            self.rest_send.commit()

            # Register the result
            action = "config_deploy"
            result = self.rest_send.result_current["success"]
            if result is False:
                self.results.diff_current = {}
            else:
                diff = {}
                diff.update({f"{action}": result})
                for serial_number in serial_numbers:
                    ip_address = self.serial_number_to_ip_address[serial_number]
                    diff.update({ip_address: serial_number})
                self.results.diff_current = diff

            self.results.action = action
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

        # Use this if we cannot update maintenance mode in frozen fabrics
        # self._can_fabric_be_deployed()
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

    @property
    def config(self):
        """
        ### Summary
        The maintenance mode configurations to be sent to the controller.

        -   getter: Return the config value.
        -   setter: Set the config value.
        -   setter: Raise ``ValueError`` if value is not a list.
        -   setter: Raise ``ValueError`` if value contains invalid content.

        ### Value structure
        value is a ``list`` of ``dict``.  Each dict must contain the following:
        -   ``deploy``: ``bool``.  If True, the switch maintenance mode
            will be deployed.
        -   ``fabric_name``: ``str``.  The name of the switch's hosting fabric.
        -   ``ip_address``: ``str``.  The ip address of the switch.
        -   ``mode``: ``str``.  The intended maintenance mode.  Must be one of
            "maintenance" or "normal".
        -   ``serial_number``: ``str``.  The serial number of the switch.

        ### Example
        ```json
        [
            {
                "deploy": false,
                "fabric_name": "MyFabric",
                "ip_address": "172.22.150.2",
                "mode": "maintenance",
                "serial_number": "FCI1234567"
            },
            {
                "deploy": true,
                "fabric_name": "YourFabric",
                "ip_address": "172.22.150.3",
                "mode": "normal",
                "serial_number": "HMD2345678"
            }
        ]
        ```
        """
        return self._properties["config"]

    @config.setter
    def config(self, value):
        try:
            self.verify_config_parameters(value)
        except ValueError as error:
            raise ValueError(error) from error
        self._properties["config"] = value

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
