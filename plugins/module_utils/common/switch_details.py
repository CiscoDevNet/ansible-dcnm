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

import inspect
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.inventory.inventory import \
    EpAllSwitches
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError


class SwitchDetails:
    """
    Retrieve switch details from the controller and provide property accessors
    for the switch attributes.

    ### Usage
    ```python
    instance = SwitchDetails()
    instance.results = Results()
    instance.rest_send = RestSend(ansible_module)
    instance.refresh()
    instance.filter = "10.1.1.1"
    fabric_name = instance.fabric_name
    serial_number = instance.serial_number
    etc...
    ```

    ### Endpoint
    ``/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/inventory/allswitches``
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED common.SwitchDetails()")

        self.conversions = ConversionUtils()
        self.ep_all_switches = EpAllSwitches()
        self.path = self.ep_all_switches.path
        self.verb = self.ep_all_switches.verb

        self._init_properties()

    def _init_properties(self):
        self.properties = {}
        self.properties["filter"] = None
        self.properties["info"] = {}
        self.properties["params"] = None

    def validate_commit_parameters(self):
        """
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

    def refresh(self):
        """
        Refresh switch_details with current switch details from
        the controller.

        ### Raises
        -   ``ControllerResponseError`` if the controller response is not 200.
        -   ``ValueError`` if mandatory parameters are not set.
        """
        method_name = inspect.stack()[0][3]

        try:
            self.validate_commit_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        # Regardless of ansible_module.check_mode, we need to get the
        # switch details. So, set check_mode to False.
        self.rest_send.check_mode = False
        self.rest_send.verb = self.verb
        self.rest_send.path = self.path
        self.rest_send.commit()

        self.results.response_current = self.rest_send.response_current
        self.results.response = self.rest_send.response_current
        self.results.result_current = self.rest_send.result_current
        self.results.result = self.rest_send.result_current

        if self.results.response_current.get("RETURN_CODE") == 200:
            self.results.failed = False
        else:
            self.results.failed = True
        # SwitchDetails never changes the controller state
        self.results.changed = False

        if self.results.response_current["RETURN_CODE"] != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Unable to retrieve switch information from the controller. "
            msg += f"Got response {self.results.response_current}"
            raise ControllerResponseError(msg)

        data = self.results.response_current.get("DATA")
        self.properties["info"] = {}
        for switch in data:
            self.properties["info"][switch["ipAddress"]] = switch

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

        if self.filter not in self.properties["info"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Switch with ip_address {self.filter} does not exist on "
            msg += "the controller."
            raise ValueError(msg)

        if item not in self.properties["info"][self.filter]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not have a key named {item}."
            raise ValueError(msg)

        return self.conversions.make_boolean(
            self.conversions.make_none(self.properties["info"][self.filter].get(item))
        )

    @property
    def filter(self):
        """
        Set the query filter.

        The filter should be the ip_address of the switch from which to
        retrieve details.

        ``filter`` must be set before accessing this class's properties.
        """
        return self.properties.get("filter")

    @filter.setter
    def filter(self, value):
        self.properties["filter"] = value

    @property
    def fabric_name(self):
        """
        -   Return the ``fabricName`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise.
        """
        return self._get("fabricName")

    @property
    def freeze_mode(self):
        """
        -   Return the ``freezeMode`` of the filtered switch's fabric,
            if it exists.
        -   Return ``None`` otherwise.
        """
        return self._get("freezeMode")

    @property
    def hostname(self):
        """
        -   Return the ``hostName`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise.

        ### NOTES
            -   ``hostname`` is None for NDFC version 12.1.2e
            -   Better to use ``logical_name`` which is populated
                in both NDFC versions 12.1.2e and 12.1.3b
        """
        return self._get("hostName")

    @property
    def info(self):
        """
        -   Return parsed data from the GET request.
        -   Return ``None`` otherwise

        NOTE: Keyed on ip_address
        """
        return self.properties["info"]

    @property
    def is_non_nexus(self):
        """
        -   Return the ``isNonNexus`` status of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        -   Example: false, true
        """
        return self._get("isNonNexus")

    @property
    def logical_name(self):
        """
        -   Return the ``logicalName`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
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
            msg += "mode is not set.  Either ``filter`` has not been "
            msg += "set, or the controller response is invalid."
            raise ValueError(msg)
        if self.system_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "system_mode is not set.  Either ``filter`` has not been "
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
        -   Return the ``managable`` status of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        -   Example: false, true
        """
        return self._get("managable")

    @property
    def mode(self):
        """
        -   Return the ``mode`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        -   ``mode`` is converted from Titlecase to lowercase.
        -   Example: maintenance, migration, normal, inconsistent
        """
        mode = self._get("mode")
        if mode is None:
            return None
        return mode.lower()

    @property
    def model(self):
        """
        -   Return the ``model`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("model")

    @property
    def oper_status(self):
        """
        -   Return the ``operStatus`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        -   Example: Minor
        """
        return self._get("operStatus")

    @property
    def platform(self):
        """
        -   Return the ``platform`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise

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
        -   Return the ``release`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        -   Example: 10.2(5)
        """
        return self._get("release")

    @property
    def rest_send(self):
        """
        An instance of the ``RestSend`` class.
        """
        return self.properties["rest_send"]

    @rest_send.setter
    def rest_send(self, value):
        self.properties["rest_send"] = value

    @property
    def results(self):
        """
        An instance of the ``Results`` class.
        """
        return self.properties["results"]

    @results.setter
    def results(self, value):
        self.properties["results"] = value

    @property
    def role(self):
        """
        -   Return the ``switchRole`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("switchRole")

    @property
    def serial_number(self):
        """
        -   Return the ``serialNumber`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("serialNumber")

    @property
    def source_interface(self):
        """
        -   Return the ``sourceInterface`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("sourceInterface")

    @property
    def source_vrf(self):
        """
        -   Return the ``sourceVrf`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("sourceVrf")

    @property
    def status(self):
        """
        -   Return the ``status`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("status")

    @property
    def switch_db_id(self):
        """
        -   Return the ``switchDbID`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("switchDbID")

    @property
    def switch_role(self):
        """
        -   Return the ``switchRole`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("switchRole")

    @property
    def switch_uuid(self):
        """
        -   Return the ``swUUID`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("swUUID")

    @property
    def switch_uuid_id(self):
        """
        -   Return the ``swUUIDId`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("swUUIDId")

    @property
    def system_mode(self):
        """
        -   Return the ``systemMode`` of the filtered switch, if it exists.
        -   Return ``None`` otherwise
        """
        return self._get("systemMode")
