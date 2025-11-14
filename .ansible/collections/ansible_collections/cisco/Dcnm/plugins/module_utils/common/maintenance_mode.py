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

# Required for class decorators
# pylint: disable=no-member

import copy
import inspect
import logging

from .api.v1.lan_fabric.rest.control.fabrics.fabrics import (
    EpFabricConfigDeploy, EpMaintenanceModeDeploy, EpMaintenanceModeDisable,
    EpMaintenanceModeEnable)
from .conversion import ConversionUtils
from .exceptions import ControllerResponseError
from .properties import Properties


@Properties.add_rest_send
@Properties.add_results
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
            -   ``commit`` if config, rest_send, or results are not set.
            -   ``commit`` if ``EpMaintenanceModeEnable`` or
                ``EpMaintenanceModeDisable`` raise ``ValueError``.
            -   ``commit``  if either ``chance_system_mode()`` or
                ``deploy_switches()`` raise ``ControllerResponseError``.

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
        self.endpoints = []

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

        self.conversion = ConversionUtils()
        self.ep_maintenance_mode_deploy = EpMaintenanceModeDeploy()
        self.ep_maintenance_mode_disable = EpMaintenanceModeDisable()
        self.ep_maintenance_mode_enable = EpMaintenanceModeEnable()
        self.ep_fabric_config_deploy = EpFabricConfigDeploy()

        self._config = None
        self._rest_send = None
        self._results = None

        msg = "ENTERED MaintenanceMode(): "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

    def verify_config_parameters(self, value) -> None:
        """
        ### Summary
        Verify that required parameters are present in config.

        ### Raises
        -   ``TypeError`` if ``config`` is not a list.
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
            raise TypeError(msg)

        for item in value:
            try:
                self.verify_deploy(item)
                self.verify_fabric_name(item)
                self.verify_ip_address(item)
                self.verify_mode(item)
                self.verify_serial_number(item)
                self.verify_wait_for_mode_change(item)
            except (TypeError, ValueError) as error:
                raise ValueError(error) from error

    def verify_deploy(self, item) -> None:
        """
        ### Summary
        Verify the ``deploy`` parameter.

        ### Raises
        -   ``ValueError`` if:
                -   ``deploy`` is not present.
        -   ``TypeError`` if:
                -   `deploy`` is not a boolean.
        """
        method_name = inspect.stack()[0][3]
        if item.get("deploy", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is missing mandatory key: deploy."
            raise ValueError(msg)
        if not isinstance(item.get("deploy", None), bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Expected boolean for deploy. "
            msg += f"Got type {type(item).__name__}, "
            msg += f"value {item.get('deploy', None)}."
            raise TypeError(msg)

    def verify_fabric_name(self, item) -> None:
        """
        ### Summary
        Validate the ``fabric_name`` parameter.

        ### Raises
        -   ``ValueError`` if:
                -   ``fabric_name`` is not present.
                -   ``fabric_name`` is not a valid fabric name.
        """
        method_name = inspect.stack()[0][3]
        if item.get("fabric_name", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is missing mandatory key: fabric_name."
            raise ValueError(msg)
        try:
            self.conversion.validate_fabric_name(item.get("fabric_name", None))
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

    def verify_ip_address(self, item) -> None:
        """
        ### Summary
        Validate the ``ip_address`` parameter.

        ### Raises
        -   ``ValueError`` if:
                -   ``ip_address`` is not present.
        """
        method_name = inspect.stack()[0][3]
        if item.get("ip_address", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is missing mandatory key: ip_address."
            raise ValueError(msg)

    def verify_mode(self, item) -> None:
        """
        ### Summary
        Validate the ``mode`` parameter.

        ### Raises
        -   ``ValueError`` if:
                -   ``mode`` is not present.
                -   ``mode`` is not one of "maintenance" or "normal".
        """
        method_name = inspect.stack()[0][3]
        if item.get("mode", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is missing mandatory key: mode."
            raise ValueError(msg)
        if item.get("mode", None) not in self.valid_modes:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"mode must be one of {' or '.join(self.valid_modes)}. "
            msg += f"Got {item.get('mode', None)}."
            raise ValueError(msg)

    def verify_serial_number(self, item) -> None:
        """
        ### Summary
        Validate the ``serial_number`` parameter.

        ### Raises
        - ``ValueError`` if:
                -   ``serial_number`` is not present.
        """
        method_name = inspect.stack()[0][3]
        if item.get("serial_number", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is missing mandatory key: serial_number."
            raise ValueError(msg)

    def verify_wait_for_mode_change(self, item) -> None:
        """
        ### Summary
        Verify the ``wait_for_mode_change`` parameter.

        ### Raises
        -   ``ValueError`` if:
                -   ``wait_for_mode_change`` is not present.
        -   ``TypeError`` if:
                -   `wait_for_mode_change`` is not a boolean.
        """
        method_name = inspect.stack()[0][3]
        if item.get("wait_for_mode_change", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is missing mandatory key: wait_for_mode_change."
            raise ValueError(msg)
        if not isinstance(item.get("wait_for_mode_change", None), bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Expected boolean for wait_for_mode_change. "
            msg += f"Got type {type(item).__name__}, "
            msg += f"value {item.get('deploy', None)}."
            raise TypeError(msg)

    def verify_commit_parameters(self) -> None:
        """
        ### Summary
        Verify that required parameters are present before calling commit.

        ### Raises
        -   ``ValueError`` if:
                -   ``config`` is not set.
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
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

    def commit(self) -> None:
        """
        ### Summary
        Initiates the maintenance mode change on the controller.

        ### Raises
        -   ``ValueError`` if
                -   ``config`` is not set.
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
                -   any exception is raised by:
                        -   ``verify_commit_parameters()``
                        -   ``change_system_mode()``
                        -   ``deploy_switches()``
        """
        try:
            self.verify_commit_parameters()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

        try:
            self.change_system_mode()
            self.deploy_switches()
        except (ControllerResponseError, ValueError, TypeError) as error:
            raise ValueError(error) from error

    def change_system_mode(self) -> None:
        """
        ### Summary
        Send the maintenance mode change request to the controller.

        ### Raises
        -   ``ControllerResponseError`` if:
                -   controller response != 200.
        -  ``ValueError`` if:
                -   ``fabric_name`` is invalid.
                -   endpoint cannot be resolved.
                -   ``Results()`` raises an exception.
        -  ``TypeError`` if:
                -   ``serial_number`` is not a string.
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
            self.rest_send.commit()

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
            try:
                self.results.action = "change_sytem_mode"
                self.results.check_mode = self.check_mode
                self.results.state = self.state
                self.results.response_current = copy.deepcopy(
                    self.rest_send.response_current
                )
                self.results.result_current = copy.deepcopy(
                    self.rest_send.result_current
                )
                self.results.register_task_result()
            except (TypeError, ValueError) as error:
                raise ValueError(error) from error

            if self.results.response_current["RETURN_CODE"] != 200:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Unable to change system mode on switch: "
                msg += f"fabric_name {fabric_name}, "
                msg += f"ip_address {ip_address}, "
                msg += f"serial_number {serial_number}. "
                msg += f"Got response {self.results.response_current}"
                raise ControllerResponseError(msg)

    def build_deploy_dict(self) -> None:
        """
        ### Summary
        -   Build the deploy_dict

        ### Raises
        None

        ### Structure
        -   key: fabric_name
        -   value: list of dict
        -   each dict contains ``serial_number`` and ``wait_for_mode_change keys``

        ### Example
        ```json
        {
            "MyFabric": [
                {
                    "serial_number": "CDM4593459",
                    "wait_for_mode_change": True
                },
                {
                    "serial_number": "CDM4593460",
                    "wait_for_mode_change": False
                }
            ],
            "YourFabric": [
                {
                    "serial_number": "DDM0455882",
                    "wait_for_mode_change": True
                },
                {
                    "serial_number": "DDM5598759",
                    "wait_for_mode_change": True
                }
            ]
        }
        """
        self.deploy_dict = {}
        for item in self.config:
            fabric_name = item.get("fabric_name")
            serial_number = item.get("serial_number")
            deploy = item.get("deploy")
            wait_for_mode_change = item.get("wait_for_mode_change")
            if fabric_name not in self.deploy_dict:
                self.deploy_dict[fabric_name] = []
            item_dict = {}
            if deploy is True:
                item_dict["serial_number"] = serial_number
                item_dict["wait_for_mode_change"] = wait_for_mode_change
                self.deploy_dict[fabric_name].append(item_dict)

    def build_serial_number_to_ip_address(self) -> None:
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

    def build_endpoints(self) -> None:
        """
        ### Summary
        Build ``endpoints`` dict used in ``self.deploy_switches``.

        ### Raises
        ``ValueError`` if endpoint configuration fails.
        """
        method_name = inspect.stack()[0][3]
        endpoints = []
        for fabric_name, switches in self.deploy_dict.items():
            for item in switches:
                endpoint = {}
                try:
                    self.ep_maintenance_mode_deploy.fabric_name = fabric_name
                    self.ep_maintenance_mode_deploy.serial_number = item["serial_number"]
                    self.ep_maintenance_mode_deploy.wait_for_mode_change = item["wait_for_mode_change"]
                except (KeyError, TypeError, ValueError) as error:
                    msg = f"{self.class_name}.{method_name}: "
                    msg += "Error resolving endpoint: "
                    msg += f"Error details: {error}."
                    raise ValueError(msg) from error
                endpoint["path"] = self.ep_maintenance_mode_deploy.path
                endpoint["verb"] = self.ep_maintenance_mode_deploy.verb
                endpoint["serial_number"] = self.ep_maintenance_mode_deploy.serial_number
                endpoint["fabric_name"] = fabric_name
                endpoints.append(copy.copy(endpoint))
        self.endpoints = copy.copy(endpoints)

    def deploy_switches(self) -> None:
        """
        ### Summary
        Initiate config-deploy for the switches in ``self.deploy_dict``.

        ### Raises
        -   ``ControllerResponseError`` if:
                -   controller response != 200.
        -   ``ValueError`` if:
                -   endpoint cannot be resolved.
        """
        method_name = inspect.stack()[0][3]
        self.build_deploy_dict()
        self.build_serial_number_to_ip_address()
        try:
            self.build_endpoints()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error building endpoints. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        for endpoint in self.endpoints:
            # Send request
            self.rest_send.path = endpoint["path"]
            self.rest_send.verb = endpoint["verb"]
            self.rest_send.payload = None
            self.rest_send.commit()

            # Register the result
            action = "deploy_maintenance_mode"
            result = self.rest_send.result_current["success"]
            if result is False:
                self.results.diff_current = {}
            else:
                diff = {}
                diff.update({f"{action}": result})
                ip_address = self.serial_number_to_ip_address[endpoint["serial_number"]]
                diff.update({ip_address: ip_address})
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
                msg += "Unable to deploy switch: "
                msg += f"fabric_name {endpoint['fabric_name']}, "
                msg += "serial_number "
                msg += f"{endpoint['serial_number']}. "
                msg += f"Got response {self.results.response_current}."
                raise ControllerResponseError(msg)

    @property
    def config(self) -> list:
        """
        ### Summary
        The maintenance mode configurations to be sent to the controller.

        ### Raises
        -   setter: ``ValueError`` if:
                -   value is not a list.
                -   value contains invalid content.

        ### getter
        Return ``config``.

        ### setter
        Set ``config``.

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
        return self._config

    @config.setter
    def config(self, value):
        try:
            self.verify_config_parameters(value)
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error
        self._config = value
