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

# Required for class decorators
# pylint: disable=no-member

import inspect
import logging

from .api.v1.lan_fabric.rest.inventory.inventory import EpAllSwitches
from .conversion import ConversionUtils
from .exceptions import ControllerResponseError
from .properties import Properties


@Properties.add_rest_send
@Properties.add_results
class SwitchDetails:
    """
    Retrieve switch details from the controller and provide property accessors
    for the switch attributes.

    ### Raises
    -   ``ControllerResponseError`` if:
            -   The controller RETURN_CODE is not 200.
    -   ``ValueError`` if:
            -   Mandatory parameters are not set.
            -   There was an error configuring ``RestSend()`` e.g. invalid
                property values, etc.

    ### Usage
    - Where ``ansible_module`` is an instance of ``AnsibleModule``

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

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED common.SwitchDetails()")

        self.action = "switch_details"
        self.conversion = ConversionUtils()
        self.ep_all_switches = EpAllSwitches()
        self._filter = None
        self._info = None
        self._rest_send = None
        self._results = None

    def validate_refresh_parameters(self) -> None:
        """
        ### Summary
        Validate that mandatory parameters are set before calling refresh().

        ### Raises
        -   ``ValueError`` if instance.rest_send is not set.
        -   ``ValueError`` if instance.results is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set before calling "
            msg += f"{self.class_name}.refresh()."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.results must be set before calling "
            msg += f"{self.class_name}.refresh()."
            raise ValueError(msg)

    def send_request(self) -> None:
        """
        ### Summary
        Send the request to the controller.

        ### Raises
        -   ``ValueError`` if the RestSend object raises
            ``TypeError`` or ``ValueError``.
        """
        # Send request
        try:
            self.rest_send.save_settings()
            self.rest_send.timeout = 1
            # Regardless of ansible_module.check_mode, we need to get the
            # switch details. So, set check_mode to False.
            self.rest_send.check_mode = False
            self.rest_send.path = self.ep_all_switches.path
            self.rest_send.verb = self.ep_all_switches.verb
            self.rest_send.commit()
            self.rest_send.restore_settings()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

    def update_results(self) -> None:
        """
        ### Summary
        Update and register the results.

        ### Raises
        -   ``ControllerResponseError`` if:
                - The controller RETURN_CODE is not 200.
        -   ``ValueError`` if:
                - ``Results()`` raises ``TypeError``.
        """
        method_name = inspect.stack()[0][3]
        # Update and register results
        try:
            self.results.action = self.action
            self.results.response_current = self.rest_send.response_current
            self.results.result_current = self.rest_send.result_current
            # SwitchDetails never changes the controller state
            self.results.changed = False

            if self.results.response_current["RETURN_CODE"] == 200:
                self.results.failed = False
            else:
                self.results.failed = True
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

    def refresh(self):
        """
        Refresh switch_details with current switch details from
        the controller.

        ### Raises
        -   ``ValueError`` if
                -   Mandatory parameters are not set.
                -   There was an error configuring RestSend() e.g.
                    invalid property values, etc.
                -   There is an error sending the request to the controller.
                -   There is an error updatingcontroller results.
        """
        method_name = inspect.stack()[0][3]
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

        data = self.results.response_current.get("DATA")
        self._info = {}
        for switch in data:
            if switch.get("ipAddress", None) is None:
                continue
            self._info[switch["ipAddress"]] = switch

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

        if self.filter not in self._info:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Switch with ip_address {self.filter} does not exist on "
            msg += "the controller."
            raise ValueError(msg)

        if item not in self._info[self.filter]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not have a key named {item}."
            raise ValueError(msg)

        return self.conversion.make_boolean(
            self.conversion.make_none(self._info[self.filter].get(item))
        )

    @property
    def filter(self):
        """
        ### Summary
        Set the query filter.

        ### Raises
        None. However, if ``filter`` is not set, or ``filter`` is set to
        a non-existent switch, ``ValueError`` will be raised when accessing
        the various getter properties.

        ### Details
        The filter should be the ip_address of the
        switch from which to retrieve details.

        ``filter`` must be set before accessing this class's properties.
        """
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value

    @property
    def fabric_name(self):
        """
        ### Summary
        The ``fabricName`` of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``fabricName`` of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("fabricName")

    @property
    def freeze_mode(self):
        """
        ### Summary
        The ``freezeMode`` of the filtered switch's fabric.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``freezeMode`` of the filtered switch's fabric,
            if it exists.
        -   ``None`` otherwise.
        """
        return self._get("freezeMode")

    @property
    def hostname(self):
        """
        ### Summary
        The ``hostName`` of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``hostName`` of the filtered switch, if it exists.
        -   ``None`` otherwise.

        ### NOTES
        -   ``hostname`` is None for NDFC version 12.1.2e
        -   Better to use ``logical_name`` which is populated
            in both NDFC versions 12.1.2e and 12.1.3b
        """
        return self._get("hostName")

    @property
    def info(self):
        """
        ### Summary
        Parsed data from the GET request.

        ### Raises
        None

        ### Returns
        -   Parsed data from the GET request, if it exists.
        -   ``None`` otherwise

        ### NOTES
        -   Keyed on ip_address
        """
        return self._info

    @property
    def is_non_nexus(self):
        """
        ### Summary
        The ``isNonNexus`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``isNonNexus`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("isNonNexus")

    @property
    def logical_name(self):
        """
        ### Summary
        The ``logicalName`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``logicalName`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("logicalName")

    @property
    def maintenance_mode(self):
        """
        ### Summary
        -   Return a synthesized value for ``maintenanceMode`` status of the
            filtered switch, if it exists.
        -   Return ``mode`` otherwise.
        -   Values:
                -   ``inconsistent``: ``mode`` and ``system_mode`` differ.
                    See NOTES.
                -   ``maintenance``: The switch is in maintenance mode.  It has
                    withdrawn its routes, etc, from the fabric so that traffic
                    does not traverse the switch.  Maintenance operations will
                    not impact traffic in the hosting fabric.
                -   ``migration``: The switch config is not compatible with the
                    switch role in the hosting fabric.  Manual remediation is
                    required.
                -   ``normal``: The switch is participating as a traffic
                    forwarding agent in the hosting fabric.

        ### Raises
        -   ``ValueError`` if ``mode`` cannot be ascertained.
        -   ``ValueError`` if ``system_mode`` cannot be ascertained.

        ### NOTES
        -   ``mode`` is the current NDFC configured value of the switch's
            ``systemMode`` (``system_mode``), whereas ``system_mode`` is the
            current value on the switch.  When these differ, NDFC displays
            ``inconsistent`` for the switch's ``maintenanceMode`` state.
            To resolve ``inconsistent`` state, a switch ``config-deploy``
            must be initiated on the controller.
        """
        method_name = inspect.stack()[0][3]
        if self.mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "mode is not set. Either 'filter' has not been "
            msg += "set, or the controller response is invalid."
            raise ValueError(msg)
        if self.system_mode is None:
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
    def managable(self):
        """
        ### Summary
        The ``managable`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``managable`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        -   Example: false, true

        ### NOTES
        -   Yes, managable is misspelled.  It is spelled this way in the
            controller response.
        """
        return self._get("managable")

    @property
    def mode(self):
        """
        ### Summary
        The ``mode`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``mode`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        -   Example: maintenance, migration, normal, inconsistent
        """
        mode = self._get("mode")
        if mode is None:
            return None
        return mode.lower()

    @property
    def model(self):
        """
        ### Summary
        The ``model`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``model`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("model")

    @property
    def oper_status(self):
        """
        ### Summary
        The ``operStatus`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``operStatus`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        -   Example: Minor
        """
        return self._get("operStatus")

    @property
    def platform(self):
        """
        ### Summary
        The ``platform`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``platform`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        -   Example: N9K (derived from N9K-C93180YC-EX)

        ### NOTES
            -   ``platform`` is derived from ``model``.
                It is not in the controller response.
        """
        model = self._get("model")
        if model is None:
            return None
        return model.split("-")[0]

    @property
    def release(self):
        """
        ### Summary
        The ``release`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``release`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        -   Example: 10.2(5)
        """
        return self._get("release")

    @property
    def role(self):
        """
        ### Summary
        The ``switchRole`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``switchRole`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        -   Example: spine

        ### NOTES
        -   ``role`` is an alias of ``switch_role``.
        """
        return self._get("switchRole")

    @property
    def serial_number(self):
        """
        ### Summary
        The ``serialNumber`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``serialNumber`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("serialNumber")

    @property
    def source_interface(self):
        """
        ### Summary
        The ``sourceInterface`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``sourceInterface`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("sourceInterface")

    @property
    def source_vrf(self):
        """
        ### Summary
        The ``sourceVrf`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``sourceVrf`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("sourceVrf")

    @property
    def status(self):
        """
        ### Summary
        The ``status`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``status`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("status")

    @property
    def switch_db_id(self):
        """
        ### Summary
        The ``switchDbID`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``switchDbID`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("switchDbID")

    @property
    def switch_role(self):
        """
        ### Summary
        The ``switchRole`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``switchRole`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("switchRole")

    @property
    def switch_uuid(self):
        """
        ### Summary
        The ``swUUID`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``swUUID`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("swUUID")

    @property
    def switch_uuid_id(self):
        """
        ### Summary
        The ``swUUIDId`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``swUUIDId`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("swUUIDId")

    @property
    def system_mode(self):
        """
        ### Summary
        The ``systemMode`` value of the filtered switch.

        ### Raises
        -   ``ValueError`` (potentially).  See ``filter`` setter
            and ``_get`` method.

        ### Returns
        -   The ``systemMode`` value of the filtered switch, if it exists.
        -   ``None`` otherwise.
        """
        return self._get("systemMode")
