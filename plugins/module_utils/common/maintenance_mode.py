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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import (
    EpFabricConfigDeploy, EpMaintenanceModeDisable, EpMaintenanceModeEnable)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError


class MaintenanceMode:
    """
    ### Summary
    -   Modify the maintenance mode state of switches.
    -   Optionally deploy the changes.

    ### Raises
    -   ``ValueError`` in the following methods:
            -   __init__() if params is missing mandatory parameters
                ``check_mode`` or ``state``.

    -   ``ValueError`` in the following properties:
            -   ``config`` if config contains invalid content.
            -   ``rest_send`` if value is not an instance of RestSend.
            -   ``results`` if value is not an instance of Results.
            -   ``commit`` if config, rest_send, or results are not set.
            -   ``commit`` if ``EpMaintenanceModeEnable`` or
                ``EpMaintenanceModeDisable`` raise ``ValueError``.

    -   ``ControllerResponseError`` in the following methods:
            -   ``commit`` if controller response != 200.

    -   ``TypeError`` in the following properties:
            -   ``rest_send`` if value is not an instance of RestSend.
            -   ``results`` if value is not an instance of Results.

    ### Details
    -   Updates MaintenanceMode().results to reflect success/failure of
        the operation on the controller.
    -   For switches that are to be deployed, initiates a per-fabric
        bulk switch config-deploy.

    ### Example value for ``config`` in the ``Usage`` section below:
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
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.params = params
        self.action = "maintenance_mode"

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params is missing mandatory parameter: check_mode."
            raise ValueError(msg)

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params is missing mandatory parameter: state."
            raise ValueError(msg)

        # Populated in build_deploy_dict()
        self.deploy_dict = {}
        self.serial_number_to_ip_address = {}

        self.valid_modes = ["maintenance", "normal"]
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
        -   ``ValueError`` if ``config`` is not set.
        -   ``ValueError`` if ``rest_send`` is not set.
        -   ``ValueError`` if ``results`` is not set.
        -   ``ValueError`` for any exception raised by
                -   ``verify_commit_parameters()``
                -   ``change_system_mode()``
                -   ``deploy_switches()``
        """
        try:
            self.verify_commit_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.change_system_mode()
            self.deploy_switches()
        except (ControllerResponseError, ValueError, TypeError) as error:
            raise ValueError(error) from error

    def change_system_mode(self):
        """
        ### Summary
        Send the maintenance mode change request to the controller.

        ### Raises
        -   ``ControllerResponseError`` if controller response != 200.
        -  ``ValueError`` if ``fabric_name`` is invalid.
        -  ``TypeError`` if ``serial_number`` is not a string.
        """
        method_name = inspect.stack()[0][3]

        for item in self.config:
            # Build endpoint
            mode = item.get("mode")
            fabric_name = item.get("fabric_name")
            ip_address = item.get("ip_address")
            serial_number = item.get("serial_number")
            if mode == "normal":
                endpoint = self.ep_maintenance_mode_disable
            else:
                endpoint = self.ep_maintenance_mode_enable

            try:
                endpoint.fabric_name = fabric_name
                endpoint.serial_number = serial_number
            except (TypeError, ValueError) as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Error resolving endpoint: "
                msg += f"Error details: {error}."
                raise ValueError(msg) from error

            # Send request
            self.rest_send.path = endpoint.path
            self.rest_send.verb = endpoint.verb
            self.rest_send.payload = None
            msg = f"ZZZ: {self.class_name}.{method_name}: HERE"
            self.log.debug(msg)
            self.rest_send.commit()

            msg = f"ZZZ: {self.class_name}.{method_name}: "
            msg += f"rest_send.response_current: {self.rest_send.response_current}"
            self.log.debug(msg)

            # Update diff
            result = self.rest_send.result_current["success"]
            if result is False:
                self.results.diff_current = {}
            else:
                self.results.diff_current = {
                    "fabric_name": fabric_name,
                    "ip_address": ip_address,
                    "maintenance_mode": mode,
                    "serial_number": serial_number,
                }

            # register result
            self.results.action = self.action
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

            if self.results.response_current["RETURN_CODE"] != 200:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Unable to change system mode on switch: "
                msg += f"fabric_name {fabric_name}, "
                msg += f"ip_address {ip_address}, "
                msg += f"serial_number {serial_number}. "
                msg += f"Got response {self.results.response_current}"
                raise ControllerResponseError(msg)

    def build_deploy_dict(self):
        """
        ### Summary
        -   Build the deploy_dict

        ### Raises
        None

        ### Structure
        -   key: fabric_name
        -   value: list of serial_numbers to deploy for each fabric

        ### Example
        ```json
        {
            "MyFabric": ["CDM4593459", "CDM4593460"],
            "YourFabric": ["CDM4593461", "CDM4593462"]
        }
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

    def build_serial_number_to_ip_address(self):
        """
        ### Summary
        Populate self.serial_number_to_ip_address dict.

        ### Raises
        None

        ### Structure
        -   key: switch serial_number
        -   value: associated switch ip_address

        ```json
        { "CDM4593459": "192.168.1.2" }
        ```
        ### Raises
        None

        ### Notes
        -   ip_address and serial_number are added to the diff in the
            ``deploy_switches()`` method.
        """
        for item in self.config:
            serial_number = item.get("serial_number")
            ip_address = item.get("ip_address")
            self.serial_number_to_ip_address[serial_number] = ip_address

    def deploy_switches(self):
        """
        ### Summary
        Initiate config-deploy for the switches in ``self.deploy_dict``.

        ### Raises
        -   ``ControllerResponseError`` if controller response != 200.
        -   ``ValueError`` if endpoint cannot be resolved.
        """
        method_name = inspect.stack()[0][3]
        self.build_deploy_dict()
        self.build_serial_number_to_ip_address()
        endpoint = EpFabricConfigDeploy()
        for fabric_name, serial_numbers in self.deploy_dict.items():
            # Build endpoint
            try:
                endpoint.fabric_name = fabric_name
                endpoint.switch_id = serial_numbers
            except (TypeError, ValueError) as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Error resolving endpoint: "
                msg += f"Error details: {error}."
                raise ValueError(msg) from error

            # Send request
            self.rest_send.path = endpoint.path
            self.rest_send.verb = endpoint.verb
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

            if self.results.response_current["RETURN_CODE"] != 200:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Unable to deploy switches: "
                msg += f"fabric_name {fabric_name}, "
                msg += "serial_numbers "
                msg += f"{','.join(serial_numbers)}. "
                msg += f"Got response {self.results.response_current}"
                raise ControllerResponseError(msg)

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
