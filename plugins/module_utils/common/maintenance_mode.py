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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.switch_details import \
    SwitchDetails
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName


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
            except ValueError as error:
                raise ValueError(error) from error

    def verify_deploy(self, item) -> None:
        """
        ### Summary
        Verify the ``deploy`` parameter.

        ### Raises
        -   ``ValueError`` if:
                -   ``deploy`` is not present.
                -   `deploy`` is not a boolean.
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
            msg += "fabric_name must be present in config."
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
            msg += "ip_address must be present in config."
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
            msg += "mode is mandatory, but is missing from the config."
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
            msg += "serial_number must be present in config."
            raise ValueError(msg)

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
        except ValueError as error:
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

    def build_deploy_dict(self) -> None:
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
        ### Summary
        An instance of the RestSend class.

        ### Raises
        -   setter: ``TypeError`` if the value is not an instance of RestSend.

        ### getter
        Return an instance of the RestSend class.

        ### setter
        Set an instance of the RestSend class.
        """
        return self._properties["rest_send"]

    @rest_send.setter
    def rest_send(self, value):
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "RestSend"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._properties["rest_send"] = value

    @property
    def results(self):
        """
        ### Summary
        An instance of the Results class.

        ### Raises
        -   setter: ``TypeError`` if the value is not an instance of Results.

        ### getter
        Return an instance of the Results class.

        ### setter
        Set an instance of the Results class.
        """
        return self._properties["results"]

    @results.setter
    def results(self, value):
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "Results"
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
        self._properties["results"] = value


class MaintenanceModeInfo:
    """
    ### Summary
    -   Retrieve the maintenance mode state of switches.

    ### Raises
    -   ``TypeError`` in the following public properties:
            -   ``config`` if value is not a list.
            -   ``rest_send`` if value is not an instance of RestSend.
            -   ``results`` if value is not an instance of Results.

    -   ``ValueError`` in the following public methods:
            -   ``refresh()`` if:
                    -    ``config`` has not been set.
                    -    ``rest_send`` has not been set.
                    -    ``results`` has not been set.

    ### Details
    Updates ``MaintenanceModeInfo().results`` to reflect success/failure of
    the operation on the controller.

    Example value for ``config`` in the ``Usage`` section below:
    ```json
    ["192.168.1.2", "192.168.1.3"]
    ```

    Example value for ``info`` in the ``Usage`` section below:
        ```json
        {
            "192.169.1.2": {
                deployment_disabled: true
                fabric_freeze_mode: true,
                fabric_name: "MyFabric",
                fabric_read_only: true
                mode: "maintenance",
                role: "spine",
                serial_number: "FCI1234567"
            },
            "192.169.1.3": {
                deployment_disabled: false,
                fabric_freeze_mode: false,
                fabric_name: "YourFabric",
                fabric_read_only: false
                mode: "normal",
                role: "leaf",
                serial_number: "FCH2345678"
            }
        }
        ```

    ### Usage
    -   Where:
            -   ``params`` is ``AnsibleModule.params``
            -   ``config`` is per the above example.
            -   ``sender`` is an instance of a Sender() class.
                See ``dcnm_sender.py`` for usage.

    ```python
    ansible_module = AnsibleModule()
    # <prepare ansible_module per your needs>
    params = AnsibleModule.params
    instance = MaintenanceModeInfo(params)

    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend()
    rest_send.sender = sender
    try:
        instance.config = config
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
    except (TypeError, ValueError) as error:
        handle_error(error)
    deployment_disabled = instance.deployment_disabled
    fabric_freeze_mode = instance.fabric_freeze_mode
    fabric_name = instance.fabric_name
    fabric_read_only = instance.fabric_read_only
    info = instance.info
    mode = instance.mode
    role = instance.role
    serial_number = instance.serial_number
    ```
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.action = "maintenance_mode_info"

        self.params = params
        self.conversions = ConversionUtils()
        self.fabric_details = FabricDetailsByName(self.params)
        self.switch_details = SwitchDetails()

        self._init_properties()

        msg = "ENTERED MaintenanceModeInfo(): "
        self.log.debug(msg)

    def _init_properties(self):
        self._properties = {}
        self._properties["config"] = None
        self._properties["info"] = None
        self._properties["rest_send"] = None
        self._properties["results"] = None

    def verify_refresh_parameters(self) -> None:
        """
        ### Summary
        Verify that required parameters are present before
        calling ``refresh()``.

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
            msg += "before calling refresh."
            raise ValueError(msg)
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set "
            msg += "before calling refresh."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.results must be set "
            msg += "before calling refresh."
            raise ValueError(msg)

    def refresh(self):
        """
        ### Summary
        Build ``self.info``, a dict containing the current maintenance mode
        status of all switches in self.config.

        ### Raises
        -   ``ValueError`` if:
                -   ``SwitchDetails()`` raises ``ControllerResponseError``
                -   ``SwitchDetails()`` raises ``ValueError``
                -   ``FabricDetails()`` raises ``ControllerResponseError``
                -   switch with ``ip_address`` does not exist on the controller.

        ### self.info structure
        info is a dict, keyed on switch_ip, where each element is a dict
        with the following structure:
        -   ``fabric_name``: The name of the switch's hosting fabric.
        -   ``freeze_mode``: The current state of the switch's hosting fabric.
            If freeze_mode is True, configuration changes cannot be made to the
            fabric or the switches within the fabric.
        -   ``mode``: The current maintenance mode of the switch.
        -   ``role``: The role of the switch in the hosting fabric.
        -   ``serial_number``: The serial number of the switch.

        ```json
        {
            "192.169.1.2": {
                fabric_deployment_disabled: true
                fabric_freeze_mode: true,
                fabric_name: "MyFabric",
                fabric_read_only: true
                mode: "maintenance",
                role: "spine",
                serial_number: "FCI1234567"
            },
            "192.169.1.3": {
                fabric_deployment_disabled: false,
                fabric_freeze_mode: false,
                fabric_name: "YourFabric",
                fabric_read_only: false
                mode: "normal",
                role: "leaf",
                serial_number: "FCH2345678"
            }
        }
        ```
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.verify_refresh_parameters()

        self.switch_details.rest_send = self.rest_send
        self.fabric_details.rest_send = self.rest_send

        self.switch_details.results = self.results
        self.fabric_details.results = self.results

        try:
            self.switch_details.refresh()
        except (ControllerResponseError, ValueError) as error:
            raise ValueError(error) from error

        try:
            self.fabric_details.refresh()
        except (ControllerResponseError, ValueError) as error:
            raise ValueError(error) from error

        info = {}
        # Populate info dict
        for ip_address in self.config:
            self.switch_details.filter = ip_address

            try:
                serial_number = self.switch_details.serial_number
            except ValueError as error:
                raise ValueError(error) from error

            if serial_number is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Switch with ip_address {ip_address} "
                msg += "does not exist on the controller."
                raise ValueError(msg)

            fabric_name = self.switch_details.fabric_name
            freeze_mode = self.switch_details.freeze_mode
            mode = self.switch_details.maintenance_mode
            role = self.switch_details.switch_role

            try:
                self.fabric_details.filter = fabric_name
            except ValueError as error:
                raise ValueError(error) from error
            fabric_read_only = self.fabric_details.is_read_only

            info[ip_address] = {}
            info[ip_address].update({"fabric_name": fabric_name})
            if freeze_mode is True:
                info[ip_address].update({"fabric_freeze_mode": True})
            else:
                info[ip_address].update({"fabric_freeze_mode": False})
            if fabric_read_only is True:
                info[ip_address].update({"fabric_read_only": True})
            else:
                info[ip_address].update({"fabric_read_only": False})
            if freeze_mode is True or fabric_read_only is True:
                info[ip_address].update({"fabric_deployment_disabled": True})
            else:
                info[ip_address].update({"fabric_deployment_disabled": False})
            info[ip_address].update({"mode": mode})
            if role is not None:
                info[ip_address].update({"role": role})
            else:
                info[ip_address].update({"role": "na"})
            info[ip_address].update({"serial_number": serial_number})
        self.info = copy.deepcopy(info)

    def _get(self, item):
        """
        Return the value of the item from the filtered switch.

        ### Raises
        -   ``ValueError`` if ``filter`` is not set.
        -   ``ValueError`` if ``filter`` is not in the controller response.
        -   ``ValueError`` if item is not in the filtered switch dict.
        """
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter before accessing "
            msg += f"property {item}."
            raise ValueError(msg)

        if self.filter not in self._properties["info"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Switch with ip_address {self.filter} does not exist on "
            msg += "the controller."
            raise ValueError(msg)

        if item not in self._properties["info"][self.filter]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not have a key named {item}."
            raise ValueError(msg)

        return self.conversions.make_boolean(
            self.conversions.make_none(self._properties["info"][self.filter].get(item))
        )

    @property
    def filter(self):
        """
        ### Summary
        Set the query filter.

        ### Raises
        None. However, if ``filter`` is not set, or ``filter`` is set to
        an ip_address for a switch that does not exist on the controller,
        ``ValueError`` will be raised when accessing the various getter
        properties.

        ### Details
        The filter should be the ip_address of the switch from which to
        retrieve details.

        ``filter`` must be set before accessing this class's properties.
        """
        return self._properties.get("filter")

    @filter.setter
    def filter(self, value):
        self._properties["filter"] = value

    @property
    def config(self) -> list:
        """
        ### Summary
        A list of switch ip addresses for which maintenance mode state
        will be retrieved.

        ### Raises
        -   setter: ``TypeError`` if:
                -   ``config`` is not a ``list``.
                -   Elements of ``config`` are not ``str``.

        ### getter
        Return ``config``.

        ### setter
        Set ``config``.

        ### Value structure
        value is a ``list`` of ip addresses

        ### Example
        ```json
        ["172.22.150.2", "172.22.150.3"]
        ```
        """
        return self._properties["config"]

    @config.setter
    def config(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.config must be a list. "
            msg += f"Got type: {type(value).__name__}."
            raise TypeError(msg)

        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += f"{self.class_name}.config must be a list of strings "
                msg += "containing ip addresses. "
                msg += f"Got type: {type(item).__name__}."
                raise TypeError(msg)
        self._properties["config"] = value

    @property
    def fabric_deployment_disabled(self):
        """
        ### Summary
        The current ``fabric_deployment_disabled`` state of the
        filtered switch's hosting fabric.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set.
                -   ``filter`` is not in the controller response.
                -   ``deployment_disabled`` is not in the filtered switch dict.

        ### Valid values
        -   ``True``: The fabric is in a state where configuration changes
            cannot be made.
        -   ``False``: The fabric is in a state where configuration changes
            can be made.
        """
        return self._get("fabric_deployment_disabled")

    @property
    def fabric_freeze_mode(self):
        """
        ### Summary
        The freezeMode state of the fabric in which the
        filtered switch resides.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set.
                -   ``filter`` is not in the controller response.
                -   ``fabric_name`` is not in the filtered switch dict.

        ### Valid values
        -   ``True``: The fabric is in a state where configuration changes
            cannot be made.
        -   ``False``: The fabric is in a state where configuration changes
            can be made.
        """
        return self._get("fabric_freeze_mode")

    @property
    def fabric_name(self):
        """
        ### Summary
        The name of the fabric in which the
        filtered switch resides.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set.
                -   ``filter`` is not in the controller response.
                -   ``fabric_name`` is not in the filtered switch dict.
        """
        return self._get("fabric_name")

    @property
    def fabric_read_only(self):
        """
        ### Summary
        The read-only state of the fabric in which the
        filtered switch resides.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set.
                -   ``filter`` is not in the controller response.
                -   ``fabric_name`` is not in the filtered switch dict.

        ### Valid values
        -   ``True``: The fabric is in a state where configuration changes
            cannot be made.
        -   ``False``: The fabric is in a state where configuration changes
            can be made.
        """
        return self._get("fabric_freeze_mode")

    @property
    def info(self) -> dict:
        """
        ### Summary
        Return or set the current maintenance mode state of the switches
        represented by the ip_addresses in self.config.

        ### Raises
        -   ``ValueError`` if:
                -   ``refresh()`` has not been called before accessing ``info``.

        ### getter
        Return ``info``.

        ### setter
        Set ``info``.

        ### ``info`` structure
        ``info`` is a dict, keyed on switch_ip, where each element is a dict
        with the following structure:
        -   ``fabric_deployment_disabled``: The current state of the switch's
            hosting fabric.  If fabric_deployment_disabled is True,
            configuration changes cannot be made to the fabric or the switches
            within the fabric.
        -   ``fabric_name``: The name of the switch's hosting fabric.
        -   ``fabric_freeze_mode``: The current state of the switch's
            hosting fabric.  If freeze_mode is True, configuration changes
            cannot be made to the fabric or the switches within the fabric.
        -   ``fabric_read_only``: The current state of the switch's
            hosting fabric.  If fabric_read_only is True, configuration changes
            cannot be made to the fabric or the switches within the fabric.
        -   ``mode``: The current maintenance mode of the switch.
        -   ``role``: The role of the switch in the hosting fabric.
        -   ``serial_number``: The serial number of the switch.

        ### Example info dict
        ```json
        {
            "192.169.1.2": {
                fabric_deployment_disabled: true
                fabric_freeze_mode: true,
                fabric_name: "MyFabric",
                fabric_read_only: true
                mode: "maintenance",
                role: "spine",
                serial_number: "FCI1234567"
            },
            "192.169.1.3": {
                fabric_deployment_disabled: false
                fabric_freeze_mode: false,
                fabric_name: "YourFabric",
                fabric_read_only: false
                mode: "normal",
                role: "leaf",
                serial_number: "FCH2345678"
            }
        }
        ```
        """
        method_name = inspect.stack()[0][3]
        if self._properties["info"] is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.refresh() must be called before "
            msg += f"accessing {self.class_name}.{method_name}."
            raise ValueError(msg)
        return copy.deepcopy(self._properties["info"])

    @info.setter
    def info(self, value: dict):
        if not isinstance(value, dict):
            msg = f"{self.class_name}.info.setter: "
            msg += "value must be a dict. "
            msg += f"Got value {value} of type {type(value).__name__}."
            raise TypeError(msg)
        self._properties["info"] = value

    @property
    def mode(self):
        """
        ### Summary
        The current maintenance mode of the filtered switch.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set.
                -   ``filter`` is not in the controller response.
                -   ``mode`` is not in the filtered switch dict.
        """
        return self._get("mode")

    @property
    def rest_send(self):
        """
        ### Summary
        An instance of the RestSend class.

        ### Raises
        -   setter: ``TypeError`` if the value is not an instance of RestSend.

        ### getter
        Return an instance of the RestSend class.

        ### setter
        Set an instance of the RestSend class.
        """
        return self._properties["rest_send"]

    @rest_send.setter
    def rest_send(self, value):
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "RestSend"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._properties["rest_send"] = value

    @property
    def results(self):
        """
        ### Summary
        An instance of the Results class.

        ### Raises
        -   setter: ``TypeError`` if the value is not an instance of Results.

        ### getter
        Return an instance of the Results class.

        ### setter
        Set an instance of the Results class.
        """
        return self._properties["results"]

    @results.setter
    def results(self, value):
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "Results"
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
        self._properties["results"] = value

    @property
    def role(self):
        """
        ### Summary
        The role of the filtered switch in the hosting fabric.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set.
                -   ``filter`` is not in the controller response.
                -   ``role`` is not in the filtered switch dict.
        """
        return self._get("role")

    @property
    def serial_number(self):
        """
        ### Summary
        The serial number of the filtered switch.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set.
                -   ``filter`` is not in the controller response.
                -   ``serial_number`` is not in the filtered switch dict.
        """
        return self._get("serial_number")
