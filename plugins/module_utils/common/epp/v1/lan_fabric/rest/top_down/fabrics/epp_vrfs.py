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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.top_down.fabrics.fabrics import \
    EpTopdownFabricsVrfs
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties


@Properties.add_rest_send
@Properties.add_results
class EppTopdownFabricsVrfs:
    """
    ### Summary
    Parent class for *FabricsVrfs() subclasses.
    See subclass docstrings for details.

    ### Raises
    None
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "topdown_fabrics_vrfs"
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED TopdownFabricsVrfs()"
        self.log.debug(msg)

        self.data = {}
        self.conversion = ConversionUtils()
        self.ep_topdown_fabrics_vrfs = EpTopdownFabricsVrfs()

        self._rest_send = None
        self._results = None
        self._result_code = None
        self._result_message = None

    def register_result(self):
        """
        ### Summary
        Update the results object with the current state of the endpoint
        and register the result.

        ### Raises
        -   ``ValueError``if:
                -    ``Results()`` raises ``TypeError``
        """
        method_name = inspect.stack()[0][3]
        try:
            self.results.action = self.action
            self.results.response_current = self.rest_send.response_current
            self.results.result_current = self.rest_send.result_current
            if self.results.response_current.get("RETURN_CODE") in [200, 400]:
                self.results.failed = False
            else:
                self.results.failed = True
            # endpoint never changes the controller state
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
        Call the controller endpoint, refresh the endpoint response, and
        populate self.data with the results.

        ### Raises
        -   ``ValueError`` if:
                -   ``validate_refresh_parameters()`` raises ``ValueError``.
                -   ``RestSend`` raises ``TypeError`` or ``ValueError``.
                -   ``register_result()`` raises ``ValueError``.

        ### Notes
        -   ``self.data`` is a dictionary of endpoint response elements, keyed on
            fabric name.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self.validate_refresh_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.ep_topdown_fabrics_vrfs.fabric_name = self.fabric_name
            self.rest_send.path = self.ep_topdown_fabrics_vrfs.path
            self.rest_send.verb = self.ep_topdown_fabrics_vrfs.verb

            # We always want to get this endpoint's current state,
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
        response_data = self.rest_send.response_current.get("DATA")
        self._result_code = self.rest_send.response_current.get("RETURN_CODE")
        if self.result_code == 400:
            # The fabric does not exist.
            self._result_message = response_data.get("message")
            self.data = {}
        elif self.result_code == 200:
            for item in self.rest_send.response_current.get("DATA", {}):
                vrf_name = item.get("vrfName", None)
                if vrf_name is None:
                    continue
                self.data[vrf_name] = item
        else:
            message = self.rest_send.response_current.get("MESSAGE")
            msg = f"Got RETURN_CODE {self.result_code} with message {message}"
            raise ValueError(msg)

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
        Return all endpoint data from the controller (i.e. self.data)

        ``refresh`` must be called before accessing this property.

        ### Raises
        None
        """
        return self.data

    @property
    def default_sg_tag(self):
        """
        ### Summary
        -   Return the value of the ``defaultSGTag``
            parameter from the filtered response, if it exists.
        -   Return None otherwise.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. TODO: need example value
        - None
        """
        item = "defaultSGTag"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def enforce(self):
        """
        ### Summary
        -   Return the value of the ``enforce`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. MyFabric
        - None
        """
        item = "enforce"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def fabric(self):
        """
        ### Summary
        -   Return the value of the ``fabric`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. MyFabric
        - None
        """
        item = "fabric"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def hierarchical_key(self):
        """
        ### Summary
        -   Return the value of the ``hierarchicalKey`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise.

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. 7
            - None
        """
        item = "hierarchicalKey"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def item_id(self):
        """
        ### Summary
        -   Return the value of the ``id`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise.

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. 7
            - None
        """
        item = "id"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def result_code(self):
        return self._result_code

    @property
    def result_message(self):
        """
        -   If the RETURN_CODE (self.result_code) == 400, result_message
            will be DATA.message.
        -   In all other cases result_message will be response.MESSAGE
        """
        return self._result_message

    @property
    def service_vrf_template(self):
        """
        ### Summary
        -   Return the value of the ``serviceVrfTemplate`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "NA"
            - None
        """
        item = "serviceVrfTemplate"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def source(self):
        """
        ### Summary
        -   Return the value of the ``source`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "NA"
            - None
        """
        item = "source"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def tenant_name(self):
        """
        ### Summary
        -   Return the value of the ``tenantName`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. MyTenant
        - None
        """
        item = "tenantName"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def vrf_id(self):
        """
        ### Summary
        -   Return the value of the ``vrfId`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise.

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. 63032
            - None
        """
        item = "vrfId"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def vrf_name(self):
        """
        ### Summary
        -   Return the value of the ``vrfName`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise.

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. MyVrf
            - None
        """
        item = "vrfName"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def vrf_status(self):
        """
        ### Summary
        -   Return the value of the ``vrfStatus`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "NA"
            - None
        """
        item = "vrfStatus"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def vrf_extension_template(self):
        """
        ### Summary
        -   Return the value of the ``vrfExtensionTemplate`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "NA"
            - None
        """
        item = "vrfExtensionTemplate"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None

    @property
    def vrf_template_config(self):
        """
        ### Summary
        -   Return the value of the ``vrfTemplateConfig`` parameter
            from the filtered response, if it exists.
        -   Return None otherwise

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "NA"
            - None
        """
        item = "vrfTemplateConfig"
        try:
            return self._get_nv_pair(item)
        except ValueError as error:
            msg = f"Failed to retrieve {item}: Error detail: {error}"
            self.log.debug(msg)
            return None


class EppFabricsVrfsByName(EppTopdownFabricsVrfs):
    """
    ### Summary
    Retrieve fabrics vrfs details from the controller and provide
    property accessors for the fabric attributes.

    ### Raises
    -   ``ValueError`` if:
            -   ``super.__init__()`` raises ``ValueError``.
            -   ``refresh_super()`` raises ``ValueError``.
            -   ``refresh()`` raises ``ValueError``.
            -   ``filter`` is not set before accessing properties.
            -   ``vrf_name`` does not exist on the controller.
            -   An attempt is made to access a key that does not exist
                for the filtered vrf_name.

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.endpoint_parsers.ep_v1_lanfabric_rest_topdown_fabrics_vrfs import FabricsVrfsByName
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = EppFabricsVrfsByName()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    instance.fabric_name = "MyFabric"
    instance.filter = "MyVrf"
    # vrfTemplate for vrf "MyVrf" in fabric "MyFabric"
    vrf_template = instance.vrf_template

    # all vrf details for "MyVrf"
    vrf_dict = instance.filtered_data
    if vrf_dict is None:
        # vrf does not exist on the controller
    # etc...
    ```

    Or:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.endpoint_parsers.ep_v1_lanfabric_rest_topdown_fabrics_vrfs import FabricsVrfsByName
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = EppFabricsVrfsByName()
    instance.fabric_name = "MyFabric"
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    all_vrfs = instance.all_data
    ```

    Where ``all_vrfs`` will be a dictionary of all vrfs within fabric
    MyFabric, keyed on vrf_name.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        super().__init__()

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED EppFabricsVrfsByName()"
        self.log.debug(msg)

        self.data_subclass = {}
        self._fabric_name = None
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

        msg = f"ZZZ: {self.class_name}.{method_name}: "
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

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} "
            msg += f"unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(
                self.data_subclass[self.filter].get(item)
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


class EppFabricsVrfsByKeyValue(EppTopdownFabricsVrfs):
    """
    ### Summary
    Retrieve fabrics vrfs details from the controller filtered by nvPair key
    and value.  Calling ``refresh`` retrieves data for all vrfs within a fabric.
    After having called ``refresh`` data for a vrf is accessed by setting
    ``filter_key`` and ``filter_value`` which sets the ``filtered_data``
    property to a dictionary containing vrfs within fabric_name
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
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.endpoint_parsers.ep_v1_lanfabric_rest_topdown_fabrics_vrfs import FabricsVrfsByKeyValue
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "query"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = EppFabricsVrfsByKeyValue()
    instance.fabric_name = "MyFabric"
    instance.filter_key = "tenantName"
    instance.filter_value = "MyTenant"
    instance.refresh()
    vrfs = instance.filtered_data
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        super().__init__()

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED EppFabricsVrfsByKeyValue() "
        self.log.debug(msg)

        self.data_subclass = {}
        self._filter_key = None
        self._filter_value = None
        self._vrf_name = None

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

        if self.fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"set {self.class_name}.fabric_name "
            msg += f"before calling {self.class_name}.refresh()."
            raise ValueError(msg)
        if self.vrf_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"set {self.class_name}.vrf_name "
            msg += f"before calling {self.class_name}.refresh()."
            raise ValueError(msg)
        if self.filter_key is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"set {self.class_name}.filter_key to a key in the response data"
            msg += f"before calling {self.class_name}.refresh()."
            raise ValueError(msg)
        if self.filter_value is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"set {self.class_name}.filter_value to a value in the response data "
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
            self.results.failed = False
            self.results.changed = False
            return
        for item, value in self.data.items():
            if value.get(self.filter_key) == self.filter_value:
                self.data_subclass[item] = value
        self.results.diff_current = self.data_subclass

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

        if self.fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.fabric_name to a fabric name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)
        if self.vrf_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.vrf_name to a fabric name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.vrf_name) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"vrf_name {self.vrf_name} "
            msg += f"does not exist within fabric_name {self.fabric_name}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(
                self.data_subclass[self.vrf_name].get(item)
            )
        )

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

    @property
    def vrf_name(self):
        """
        ### Summary
        The VRF within fabric_name to query.

        ### Raises
        None
        """
        return self._vrf_name

    @vrf_name.setter
    def vrf_name(self, value):
        self._vrf_name = value
