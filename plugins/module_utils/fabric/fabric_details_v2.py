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

import copy
import inspect
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabrics
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties


@Properties.add_rest_send
@Properties.add_results
class FabricDetails:
    """
    ### Summary
    Parent class for *FabricDetails() subclasses.
    See subclass docstrings for details.

    ### Raises
    -   ``ValueError`` if:
            -   Mandatory properties are not set.
            -   RestSend object raises ``TypeError`` or ``ValueError``.
            -   ``params`` is missing ``check_mode`` key.
            -   ``params`` is missing ``state`` key.

    params is AnsibleModule.params
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]
        self.params = params
        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "check_mode is missing from params. "
            msg += f"params: {params}."
            raise ValueError(msg)

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "state is missing from params. "
            msg += f"params: {params}."
            raise ValueError(msg)

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED FabricDetails() (v2)"
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.data = {}
        self.conversion = ConversionUtils()
        self.ep_fabrics = EpFabrics()

    def register_result(self):
        """
        ### Summary
        Update the results object with the current state of the fabric
        details and register the result.

        ### Raises

        """
        self.results.action = "fabric_details"
        self.results.response_current = self.rest_send.response_current
        self.results.result_current = self.rest_send.result_current
        if self.results.response_current.get("RETURN_CODE") == 200:
            self.results.failed = False
        else:
            self.results.failed = True
        # FabricDetails never changes the controller state
        self.results.changed = False
        self.results.register_task_result()

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

    def refresh_super(self):
        """
        ### Summary
        Refresh the fabric details from the controller and
        populate self.data with the results.

        ### Raises
        -   ``ValueError`` if the RestSend object raises
            ``TypeError`` or ``ValueError``.

        ### Notes
        -   ``self.data`` is a dictionary of fabric details, keyed on
            fabric name.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self.validate_refresh_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.rest_send.path = self.ep_fabrics.path
            self.rest_send.verb = self.ep_fabrics.verb

            # We always want to get the controller's current fabric state,
            # regardless of the current value of check_mode.
            # We save the current check_mode and timeout settings, set
            # rest_send.check_mode to False so the request will be sent
            # to the controller, and then restore the original settings.

            self.rest_send.save_settings()
            self.rest_send.check_mode = False
            self.rest_send.timeout = 1
            self.rest_send.commit()
            self.rest_send.restore_settings()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

        self.data = {}
        if self.rest_send.response_current.get("DATA") is None:
            # The DATA key should always be present. We should never hit this.
            return
        for item in self.rest_send.response_current.get("DATA"):
            fabric_name = item.get("nvPairs", {}).get("FABRIC_NAME", None)
            if fabric_name is None:
                return
            self.data[fabric_name] = item

        self.register_result()

        msg = f"{self.class_name}.{method_name}: calling self.rest_send.commit() DONE"
        self.log.debug(msg)

    def _get(self, item):
        """
        overridden in subclasses
        """

    def _get_nv_pair(self, item):
        """
        overridden in subclasses
        """

    @property
    def all_data(self):
        """
        Return all fabric details from the controller (i.e. self.data)
        """
        return self.data

    @property
    def asn(self):
        """
        Return the BGP asn of the fabric specified with filter, if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - e.g. 65000
            - None
        """
        try:
            return self._get("asn")
        except ValueError as error:
            msg = f"Failed to retrieve asn: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def deployment_freeze(self):
        """
        Return the nvPairs.DEPLOYMENT_FREEZE of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - true
            - false
        """
        try:
            return self._get_nv_pair("DEPLOYMENT_FREEZE")
        except ValueError as error:
            msg = f"Failed to retrieve deployment_freeze: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def enable_pbr(self):
        """
        Return the PBR enable state of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: boolean
        Possible values:
            - True
            - False
            - None
        """
        try:
            return self._get_nv_pair("ENABLE_PBR")
        except ValueError as error:
            msg = f"Failed to retrieve enable_pbr: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def fabric_id(self):
        """
        Return the fabricId of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - e.g. FABRIC-5
            - None
        """
        try:
            return self._get("fabricId")
        except ValueError as error:
            msg = f"Failed to retrieve fabric_id: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def fabric_type(self):
        """
        Return the nvPairs.FABRIC_TYPE of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - Switch_Fabric
            - None
        """
        try:
            return self._get_nv_pair("FABRIC_TYPE")
        except ValueError as error:
            msg = f"Failed to retrieve fabric_type: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def is_read_only(self):
        """
        Return the nvPairs.IS_READ_ONLY of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - true
            - false
        """
        try:
            return self._get_nv_pair("IS_READ_ONLY")
        except ValueError as error:
            msg = f"Failed to retrieve is_read_only: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def replication_mode(self):
        """
        Return the nvPairs.REPLICATION_MODE of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - Ingress
            - Multicast
            - None
        """
        try:
            return self._get_nv_pair("REPLICATION_MODE")
        except ValueError as error:
            msg = f"Failed to retrieve replication_mode: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def template_name(self):
        """
        Return the templateName of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - Easy_Fabric
            - TODO - add other values
            - None
        """
        try:
            return self._get("templateName")
        except ValueError as error:
            msg = f"Failed to retrieve template_name: Error detail: {error}"
            self.log.debug(msg)
            return None


class FabricDetailsByName(FabricDetails):
    """
    Retrieve fabric details from the controller and provide
    property accessors for the fabric attributes.

    Usage (where params is AnsibleModule.params):

    ```python
    params = {"check_mode": False, "state": "merged"}
    sender = Sender() # class implementing the sender interface
    sender.ansible_module = ansible_module

    rest_send = RestSend()
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricDetailsByName(params)
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    instance.filter = "MyFabric"
    # BGP AS for fabric "MyFabric"
    bgp_as = instance.asn

    # all fabric details for "MyFabric"
    fabric_dict = instance.filtered_data
    if fabric_dict is None:
        # fabric does not exist on the controller
    # etc...
    ```

    Or:

    ```python
    sender = Sender() # class that implements the sender interface
    sender.ansible_module = ansible_module

    rest_send = RestSend()
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricDetailsByName(params)
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    all_fabrics = instance.all_data
    ```

    - Where ``all_fabrics`` will be a dictionary of all fabrics
    on the controller, keyed on fabric name.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        try:
            super().__init__(params)
        except ValueError as error:
            msg = "FabricDetailsByName.__init__: "
            msg += "Failed in super().__init__(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED FabricDetailsByName() "
        msg += f"params {params}."
        self.log.debug(msg)

        self.data_subclass = {}
        self._filter = None

    def refresh(self):
        """
        ### Refresh fabric_name current details from the controller

        ### Raises
        -   ``ValueError`` if:
                -   Mandatory properties are not set.
        """
        try:
            self.refresh_super()
        except ValueError as error:
            msg = "Failed to refresh fabric details: "
            msg += f"Error detail: {error}."
            raise ValueError(msg) from error

        self.data_subclass = copy.deepcopy(self.data)

    def _get(self, item):
        """
        Retrieve the value of the top-level (non-nvPair) item for fabric_name
        (anything not in the nvPairs dictionary).

        -   raise ``ValueError`` if ``self.filter`` has not been set.
        -   raise ``ValueError`` if ``self.filter`` (fabric_name) does not exist
            on the controller.
        -   raise ``ValueError`` if item is not a valid property name for the fabric.

        See also: ``_get_nv_pair()``
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.filter {self.filter} "
        self.log.debug(msg)

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} does not exist on the controller."
            raise ValueError(msg)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(self.data_subclass[self.filter].get(item))
        )

    def _get_nv_pair(self, item):
        """
        # Retrieve the value of the nvPair item for fabric_name.

        - raise ``ValueError`` if ``self.filter`` has not been set.
        - raise ``ValueError`` if ``self.filter`` (fabric_name) does not exist on the controller.
        - raise ``ValueError`` if item is not a valid property name for the fabric.

        See also: ``self._get()``
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.filter {self.filter} "
        self.log.debug(msg)

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} "
            msg += "does not exist on the controller."
            raise ValueError(msg)

        if self.data_subclass[self.filter].get("nvPairs", {}).get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} "
            msg += f"unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(
                self.data_subclass[self.filter].get("nvPairs").get(item)
            )
        )

    @property
    def filtered_data(self):
        """
        - Return a dictionary of the fabric matching self.filter.
        - Return None if the fabric does not exist on the controller.
        - raise ``ValueError`` if self.filter has not been set.
        """
        method_name = inspect.stack()[0][3]
        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.filter must be set before calling "
            msg += f"{self.class_name}.filtered_data"
            raise ValueError(msg)
        return self.data_subclass.get(self.filter, None)

    @property
    def filter(self):
        """
        ### Summary
        Set the fabric_name of the fabric to query.

        ### Raises
        None

        ### NOTES
        ``filter`` must be set before accessing this class's properties.
        """
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value


class FabricDetailsByNvPair(FabricDetails):
    """
    ### Summary
    Retrieve fabric details from the controller filtered by nvPair key
    and value.  Calling ``refresh`` retrieves data for all fabrics.
    After having called ``refresh`` data for a fabric accessed by setting
    ``filter_key`` and ``filter_value`` which sets the ``filtered_data``
    property to a dictionary containing fabrics on the controller
    that match ``filter_key`` and ``filter_value``.

    ### Usage
    ```python
    params = {"check_mode": False, "state": "query"}
    sender = Sender() # class implementing the sender interface
    sender.ansible_module = ansible_module

    rest_send = RestSend()
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricDetailsNvPair(params)
    instance.refresh()
    instance.filter_key = "DCI_SUBNET_RANGE"
    instance.filter_value = "10.33.0.0/16"
    fabrics = instance.filtered_data
    ```
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        try:
            super().__init__(params)
        except ValueError as error:
            msg = "FabricDetailsByNvPair.__init__: "
            msg += "Failed in super().__init__(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED FabricDetailsByNvPair() "
        self.log.debug(msg)

        self.data_subclass = {}
        self._filter_key = None
        self._filter_value = None

    def refresh(self):
        """
        ### Summary
        Refresh fabric_name current details from the controller.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter_key`` has not been set.
                -   ``filter_value`` has not been set.
        """
        method_name = inspect.stack()[0][3]

        if self.filter_key is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"set {self.class_name}.filter_key to a nvPair key "
            msg += f"before calling {self.class_name}.refresh()."
            raise ValueError(msg)
        if self.filter_value is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"set {self.class_name}.filter_value to a nvPair value "
            msg += f"before calling {self.class_name}.refresh()."
            raise ValueError(msg)

        try:
            self.refresh_super()
        except ValueError as error:
            msg = "Failed to refresh fabric details: "
            msg += f"Error detail: {error}."
            raise ValueError(msg) from error

        for item, value in self.data.items():
            if value.get("nvPairs", {}).get(self.filter_key) == self.filter_value:
                self.data_subclass[item] = value

    @property
    def filtered_data(self):
        """
        ### Summary
        A dictionary of the fabric(s) matching ``filter_key`` and
        ``filter_value``.

        ### Raises
        None

        ### Returns
        -   A ``dict`` of the fabric(s) matching ``filter_key`` and
            ``filter_value``.
        -   An empty ``dict`` if the fabric does not exist on the controller.
        """
        return self.data_subclass

    @property
    def filter_key(self):
        """
        ### Summary
        The nvPairs key on which to filter.

        ### Raises
        None

        ### Notes
        ``filter_key``should be an exact match for the key in the nvPairs
        dictionary for the fabric.
        """
        return self._filter_key

    @filter_key.setter
    def filter_key(self, value):
        self._filter_key = value

    @property
    def filter_value(self):
        """
        ### Summary
        The nvPairs value on which to filter.

        ### Raises
        None

        ### Notes
        ``filter_value`` should be an exact match for the value in the nvPairs
        dictionary for the fabric.
        """
        return self._filter_value

    @filter_value.setter
    def filter_value(self, value):
        self._filter_value = value
