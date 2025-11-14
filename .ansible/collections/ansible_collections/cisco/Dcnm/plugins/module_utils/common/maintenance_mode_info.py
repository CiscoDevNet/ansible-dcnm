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

from .conversion import ConversionUtils
from .exceptions import ControllerResponseError
from .properties import Properties
from .switch_details import SwitchDetails
from ..fabric.fabric_details_v2 import FabricDetailsByName


@Properties.add_rest_send
@Properties.add_results
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
                See ``sender_dcnm.py`` for usage.

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
        self.conversion = ConversionUtils()
        self.fabric_details = FabricDetailsByName()
        self.switch_details = SwitchDetails()

        self._config = None
        self._filter = None
        self._info = None
        self._rest_send = None
        self._results = None

        msg = "ENTERED MaintenanceModeInfo(): "
        self.log.debug(msg)

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

        try:
            self.switch_details.rest_send = self.rest_send
            self.fabric_details.rest_send = self.rest_send

            self.switch_details.results = self.results
            self.fabric_details.results = self.results
        except TypeError as error:
            raise ValueError(error) from error

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
                msg += "does not exist on the controller, or is missing its "
                msg += "serialNumber key."
                raise ValueError(msg)

            try:
                fabric_name = self.switch_details.fabric_name
                freeze_mode = self.switch_details.freeze_mode
                mode = self.switch_details.maintenance_mode
                role = self.switch_details.switch_role
            except ValueError as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Error setting properties for switch with ip_address "
                msg += f"{ip_address}. "
                msg += f"Error details: {error}"
                raise ValueError(msg) from error

            try:
                self.fabric_details.filter = fabric_name
            except ValueError as error:
                raise ValueError(error) from error

            fabric_read_only = self.fabric_details.is_read_only

            info[ip_address] = {}
            info[ip_address].update({"fabric_name": fabric_name})
            info[ip_address].update({"ip_address": ip_address})

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
        -   ``ValueError`` if:
                -   ``filter`` is not set.
                -   ``filter`` is not in the controller response.
        ### NOTES
        -   We do not need to check that ``item`` exists in the filtered
            switch dict, since ``refresh()`` has already done so.
        """
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter before accessing "
            msg += f"property {item}."
            raise ValueError(msg)

        if self.filter not in self._info:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Switch with ip_address {self.filter} does not exist on "
            msg += "the controller."
            raise ValueError(msg)

        return self.conversion.make_boolean(
            self.conversion.make_none(self._info[self.filter].get(item))
        )

    @property
    def filter(self):
        """
        ### Summary
        Set the query filter (switch IP address)

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
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value

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
        return self._config

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
                msg += "config must be a list of strings "
                msg += "containing ip addresses. "
                msg += "value contains element of type "
                msg += f"{type(item).__name__}. "
                msg += f"value: {value}."
                raise TypeError(msg)
        self._config = value

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
        return self._get("fabric_read_only")

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
        if self._info is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.refresh() must be called before "
            msg += f"accessing {self.class_name}.{method_name}."
            raise ValueError(msg)
        return copy.deepcopy(self._info)

    @info.setter
    def info(self, value: dict):
        if not isinstance(value, dict):
            msg = f"{self.class_name}.info.setter: "
            msg += "value must be a dict. "
            msg += f"Got value {value} of type {type(value).__name__}."
            raise TypeError(msg)
        self._info = value

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
