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

from ..common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabrics
from ..common.conversion import ConversionUtils
from ..common.properties import Properties


@Properties.add_rest_send
@Properties.add_results
class FabricDetails:
    """
    ### Summary
    Parent class for *FabricDetails() subclasses.
    See subclass docstrings for details.

    ### Raises
    None
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "fabric_details"
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED FabricDetails() (v2)"
        self.log.debug(msg)

        self.data = {}
        self.conversion = ConversionUtils()
        self.ep_fabrics = EpFabrics()

        self._rest_send = None
        self._results = None

    def register_result(self):
        """
        ### Summary
        Update the results object with the current state of the fabric
        details and register the result.

        ### Raises
        -   ``ValueError``if:
                -    ``Results()`` raises ``TypeError``
        """
        method_name = inspect.stack()[0][3]
        try:
            self.results.action = self.action
            self.results.response_current = self.rest_send.response_current
            self.results.result_current = self.rest_send.result_current
            if self.results.response_current.get("RETURN_CODE") == 200:
                self.results.failed = False
            else:
                self.results.failed = True
            # FabricDetails never changes the controller state
            self.results.changed = False
            self.results.register_task_result()
        except TypeError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Failed to register result. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def validate_refresh_parameters(self) -> None:
        """
        ### Summary
        Validate that mandatory parameters are set before calling refresh().

        ### Raises
        -   ``ValueError``if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
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
        -   ``ValueError`` if:
                -   ``validate_refresh_parameters()`` raises ``ValueError``.
                -   ``RestSend`` raises ``TypeError`` or ``ValueError``.
                -   ``register_result()`` raises ``ValueError``.

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

        try:
            self.register_result()
        except ValueError as error:
            raise ValueError(error) from error

        msg = f"{self.class_name}.{method_name}: calling self.rest_send.commit() DONE"
        self.log.debug(msg)

    def _get(self, item):
        """
        ### Summary
        overridden in subclasses
        """

    def _get_nv_pair(self, item):
        """
        ### Summary
        overridden in subclasses
        """

    @property
    def all_data(self):
        """
        ### Summary
        Return all fabric details from the controller (i.e. self.data)

        ``refresh`` must be called before accessing this property.

        ### Raises
        None
        """
        return self.data

    @property
    def asn(self):
        """
        ### Summary
        Return the BGP asn of the fabric specified with filter, if it exists.
        Return None otherwise.

        This is an alias of BGP_AS.

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "65000"
            - None
        """
        try:
            return self._get_nv_pair("BGP_AS")
        except ValueError as error:
            msg = f"Failed to retrieve asn: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def bgp_as(self):
        """
        ### Summary
        Return ``nvPairs.BGP_AS`` of the fabric specified with filter, if it exists.
        Return None otherwise

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "65000"
            - None
        """
        try:
            return self._get_nv_pair("BGP_AS")
        except ValueError as error:
            msg = f"Failed to retrieve bgp_as: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def deployment_freeze(self):
        """
        ### Summary
        The nvPairs.DEPLOYMENT_FREEZE of the fabric specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - False
        - True
        - None
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
        ### Summary
        The PBR enable state of the fabric specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - False
        - True
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
        ### Summary
        The ``fabricId`` value of the fabric specified with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
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
        ### Summary
        The ``nvPairs.FABRIC_TYPE`` value of the fabric specified with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. Switch_Fabric
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
        ### Summary
        The ``nvPairs.IS_READ_ONLY`` value of the fabric specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - True
        - False
        - None
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
        ### Summary
        The ``nvPairs.REPLICATION_MODE`` value of the fabric specified
        with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
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
        ### Summary
        The ``templateName`` value of the fabric specified
        with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. Easy_Fabric
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
    ### Summary
    Retrieve fabric details from the controller and provide
    property accessors for the fabric attributes.

    ### Raises
    -   ``ValueError`` if:
            -   ``super.__init__()`` raises ``ValueError``.
            -   ``refresh_super()`` raises ``ValueError``.
            -   ``refresh()`` raises ``ValueError``.
            -   ``filter`` is not set before accessing properties.
            -   ``fabric_name`` does not exist on the controller.
            -   An attempt is made to access a key that does not exist
                for the filtered fabric.

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricDetailsByName()
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
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricDetailsByName()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    all_fabrics = instance.all_data
    ```

    Where ``all_fabrics`` will be a dictionary of all fabrics on the
    controller, keyed on fabric name.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        super().__init__()

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED FabricDetailsByName()"
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
        ### Summary
        Retrieve the value of the nvPair item for fabric_name.

        ### Raises
        - ``ValueError`` if:
                -   ``self.filter`` has not been set.
                -   ``self.filter`` (fabric_name) does not exist on the controller.
                -   ``item`` is not a valid property name for the fabric.

        ### See also
        ``self._get()``
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
        ### Summary
        The DATA portion of the dictionary for the fabric specified with filter.

        ### Raises
        -   ``ValueError`` if:
                -   ``self.filter`` has not been set.

        ### Returns
        - A dictionary of the fabric matching self.filter.
        - ``None``, if the fabric does not exist on the controller.
        """
        method_name = inspect.stack()[0][3]
        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.filter must be set before accessing "
            msg += f"{self.class_name}.filtered_data."
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

    ### Raises
    -   ``ValueError`` if:
            -   ``super.__init__()`` raises ``ValueError``.
            -   ``refresh_super()`` raises ``ValueError``.
            -   ``refresh()`` raises ``ValueError``.
            -   ``filter_key`` is not set before calling ``refresh()``.
            -   ``filter_value`` is not set before calling ``refresh()``.

    ### Usage
    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "query"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricDetailsNvPair()
    instance.filter_key = "DCI_SUBNET_RANGE"
    instance.filter_value = "10.33.0.0/16"
    instance.refresh()
    fabrics = instance.filtered_data
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        super().__init__()

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
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        if len(self.data) == 0:
            self.results.diff = {}
            self.results.response = self.rest_send.response_current
            self.results.result = self.rest_send.result_current
            self.results.failed = True
            self.results.changed = False
            return
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
        The ``nvPairs`` key on which to filter.

        ### Raises
        None

        ### Notes
        ``filter_key``should be an exact match for the key in the ``nvPairs``
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
        The ``nvPairs`` value on which to filter.

        ### Raises
        None

        ### Notes
        ``filter_value`` should be an exact match for the value in the ``nvPairs``
        dictionary for the fabric.
        """
        return self._filter_value

    @filter_value.setter
    def filter_value(self, value):
        self._filter_value = value
