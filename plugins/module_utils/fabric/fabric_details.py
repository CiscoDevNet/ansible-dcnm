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

import copy
import inspect
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.rest.control.fabrics import \
    EpFabrics
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon


class FabricDetails(FabricCommon):
    """
    # Parent class for *FabricDetails() subclasses.

    See subclass docstrings for details.

    params is AnsibleModule.params
    """

    def __init__(self, params):
        super().__init__(params)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED FabricDetails()"
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.data = {}
        self.results = Results()
        self.conversion = ConversionUtils()
        self.ep_fabrics = EpFabrics()

    def _update_results(self):
        """
        Update the results object with the current state of the fabric
        details.
        """
        self.results.response_current = self.rest_send.response_current
        self.results.response = self.rest_send.response_current
        self.results.result_current = self.rest_send.result_current
        self.results.result = self.rest_send.result_current
        if self.results.response_current.get("RETURN_CODE") == 200:
            self.results.failed = False
        else:
            self.results.failed = True
        # FabricDetails never changes the controller state
        self.results.changed = False

    def refresh_super(self):
        """
        Refresh the fabric details from the controller and
        populate self.data with the results.

        self.data is a dictionary of fabric details, keyed on
        fabric name.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.rest_send.path = self.ep_fabrics.path
        self.rest_send.verb = self.ep_fabrics.verb

        # We always want to get the controller's current fabric state,
        # regardless of the current value of check_mode.
        # We save the current check_mode value, set rest_send.check_mode
        # to False so the request will be sent to the controller, and then
        # restore the original check_mode value.
        msg = f"{self.class_name}.{method_name}: calling self.rest_send.commit()"
        self.log.debug(msg)
        save_check_mode = self.rest_send.check_mode
        self.rest_send.check_mode = False
        self.rest_send.timeout = 1
        self.rest_send.commit()
        self.rest_send.check_mode = save_check_mode

        self.data = {}
        if self.rest_send.response_current.get("DATA") is None:
            # The DATA key should always be present. We should never hit this.
            self._update_results()
            return
        for item in self.rest_send.response_current.get("DATA"):
            fabric_name = item.get("nvPairs", {}).get("FABRIC_NAME", None)
            if fabric_name is None:
                self._update_results()
                return
            self.data[fabric_name] = item

        msg = f"{self.class_name}.{method_name}: calling self.rest_send.commit() DONE"
        self.log.debug(msg)

        self._update_results()

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
    instance = FabricDetailsByName(params)
    instance.rest_send = RestSend(ansible_module)
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
    instance.FabricDetailsByName(module)
    instance.rest_send = RestSend(ansible_module)
    instance.refresh()
    all_fabrics = instance.all_data
    ```

    - Where ``all_fabrics`` will be a dictionary of all fabrics
    on the controller, keyed on fabric name.
    """

    def __init__(self, params):
        super().__init__(params)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricDetailsByName()")

        self.data_subclass = {}
        self._properties["filter"] = None

    def refresh(self):
        """
        Refresh fabric_name current details from the controller
        """
        self.refresh_super()
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
        Set the fabric_name of the fabric to query.

        This needs to be set before accessing this class's properties.
        """
        return self._properties.get("filter")

    @filter.setter
    def filter(self, value):
        self._properties["filter"] = value


class FabricDetailsByNvPair(FabricDetails):
    """
    Retrieve fabric details from the controller filtered
    by nvPair key and value.  This sets the filtered_data
    property to a dictionary of all fabrics on the controller
    that match filter_key and filter_value.

    Usage (where params is AnsibleModule.params):

    instance = FabricDetailsNvPair(params)
    instance.refresh()
    instance.filter_key = "DCI_SUBNET_RANGE"
    instance.filter_value = "10.33.0.0/16"
    fabrics = instance.filtered_data
    """

    def __init__(self, params):
        super().__init__(params)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricDetailsByNvPair()")

        self.data_subclass = {}
        self._properties["filter_key"] = None
        self._properties["filter_value"] = None

    def refresh(self):
        """
        Refresh fabric_name current details from the controller.

        - raise ValueError if self.filter_key has not been set.
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

        self.refresh_super()
        for item, value in self.data.items():
            if value.get("nvPairs", {}).get(self.filter_key) == self.filter_value:
                self.data_subclass[item] = value

    @property
    def filtered_data(self):
        """
        -   Return a ``dict`` of the fabric(s) matching ``self.filter_key``
            and ``self.filter_value``.
        -   Return an empty ``dict`` if the fabric does not exist on
            the controller.
        """
        return self.data_subclass

    @property
    def filter_key(self):
        """
        - getter: Return the nvPairs key to filter on.
        - setter: Set the nvPairs key to filter on.

        This should be an exact match for the key in the nvPairs
        dictionary for the fabric.
        """
        return self._properties.get("filter_key")

    @filter_key.setter
    def filter_key(self, value):
        self._properties["filter_key"] = value

    @property
    def filter_value(self):
        """
        - getter: Return the nvPairs value to filter on.
        - setter: Set the nvPairs value to filter on.

        This should be an exact match for the value in the nvPairs
        dictionary for the fabric.
        """
        return self._properties.get("filter_value")

    @filter_value.setter
    def filter_value(self, value):
        self._properties["filter_value"] = value
