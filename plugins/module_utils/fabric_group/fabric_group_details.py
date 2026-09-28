#
# Copyright (c) 2025 Cisco and/or its affiliates.
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
# pylint: disable=too-many-instance-attributes
"""
Provides one public class:
-   FabricGroupDetails
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging
from typing import Union

from ..common.api.onemanage.endpoints import EpOneManageFabricDetails
from ..common.conversion import ConversionUtils
from ..common.operation_type import OperationType
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results
from .fabric_groups import FabricGroups


class FabricGroupDetails:
    """
    ### Summary
    Retrieve fabric group details from the controller and provide
    property accessors for the fabric group attributes.

    ### Raises
    -   ``ValueError`` if:
            -   ``refresh()`` raises ``ValueError``.
            -   ``fabric_group_name`` is not set before accessing properties.
            -   ``fabric_name`` does not exist on the controller.
            -   An attempt is made to access a key that does not exist
                for the filtered fabric.

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricGroupDetails()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    instance.fabric_group_name = "MyFabricGroup"  # set the fabric_group_name to query
    # BGP AS for fabric "MyFabricGroup"
    bgp_as = instance.asn

    # all fabric details for "MyFabricGroup"
    fabric_dict = instance.filtered_data
    if fabric_dict is None:
        # fabric does not exist on the controller
    # etc...
    ```

    Or:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = FabricGroupDetails()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    all_fabric_groups = instance.all_data
    ```

    Where ``all_fabric_groups`` will be a dictionary of all fabric groups on the
    controller, keyed on fabric group name.
    """

    def __init__(self) -> None:
        self.class_name: str = self.__class__.__name__

        self.action: str = "fabric_group_details"
        self.operation_type: OperationType = OperationType.QUERY

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED FabricGroupDetails"
        self.log.debug(msg)

        self.data: dict = {}
        self.data_subclass: dict = {}
        self.conversion: ConversionUtils = ConversionUtils()
        self.ep_onemanage_fabric_group_details: EpOneManageFabricDetails = EpOneManageFabricDetails()

        self._fabric_group_name: str = ""
        self._refreshed: bool = False
        self._rest_send: Union[RestSend, None] = None
        self._results: Union[Results, None] = None

    def _register_result(self) -> None:
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
            self.results.response_current = self.rest_send.response_current
            self.results.result_current = self.rest_send.result_current
            if self.results.response_current.get("RETURN_CODE") == 200:
                self.results.add_failed(False)
            else:
                self.results.add_failed(True)
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
        # method_name = inspect.stack()[0][3]
        # if self._rest_send is None:
        #     msg = f"{self.class_name}.{method_name}: "
        #     msg += f"{self.class_name}.rest_send must be set before calling "
        #     msg += f"{self.class_name}.refresh()."
        #     self.log.debug(msg)
        #     raise ValueError(msg)
        # if self._results is None:
        #     msg = f"{self.class_name}.{method_name}: "
        #     msg += f"{self.class_name}.results must be set before calling "
        #     msg += f"{self.class_name}.refresh()."
        #     self.log.debug(msg)
        #     raise ValueError(msg)

    def _build_data(self) -> None:
        """
        # Summary

        Build self.data from the rest_send.response_current.
        """
        method_name = inspect.stack()[0][3]

        self.data = {}
        new_data: dict = {}
        if isinstance(self.rest_send.response_current["DATA"], dict):
            new_data = self.rest_send.response_current["DATA"]
            new_data["message"] = self.rest_send.response_current["MESSAGE"]
            data = [new_data]
        elif isinstance(self.rest_send.response_current["DATA"], list):
            data = self.rest_send.response_current["DATA"]
            for item in data:
                item["message"] = self.rest_send.response_current["MESSAGE"]
        else:
            message = self.rest_send.response_current["DATA"]
            new_data["message"] = message
            data = [new_data]
        for item in data:
            fabric_group_name = item.get("nvPairs", {}).get("FABRIC_NAME", None)
            if fabric_group_name is None:
                self.data["NO_FABRIC_GROUPS_FOUND"] = item
                msg = f"{self.class_name}.{method_name}: "
                msg += "No fabric groups found in response "
                msg += f"self.data: {self.data}"
                self.log.debug(msg)
                return
            self.data[fabric_group_name] = item

    def fabric_group_exists(self, fabric_group_name: str) -> bool:
        """
        # Summary

        Check whether the specified fabric group name exists on the controller.

        ## Raises

        None

        ## Returns
        -   True if the fabric group exists on the controller.
        -   False otherwise.
        """
        instance = FabricGroups()
        instance.rest_send = self.rest_send
        instance.results = Results()
        instance.refresh()
        if fabric_group_name in instance.fabric_group_names:
            return True
        return False

    def refresh(self) -> None:
        """
        ### Summary
        Refresh fabric_group_name current details from the controller.

        ### Raises
        -   ``ValueError`` if:
                -   Mandatory properties are not set.
                -   ``validate_refresh_parameters()`` raises ``ValueError``.
                -   ``RestSend`` raises ``TypeError`` or ``ValueError``.
                -   ``_register_result()`` raises ``ValueError``.

        ### Notes
        -   ``self.data`` is a dictionary of fabric details, keyed on
            fabric name.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if self._rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set before calling "
            msg += f"{self.class_name}.refresh()."
            self.log.debug(msg)
            raise ValueError(msg)
        if self._results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.results must be set before calling "
            msg += f"{self.class_name}.refresh()."
            self.log.debug(msg)
            raise ValueError(msg)

        if not self.fabric_group_exists(self.fabric_group_name):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Fabric group {self.fabric_group_name} does not exist on the controller."
            self.log.debug(msg)
            self.data = {}
            self._refreshed = True
            return

        try:
            self.rest_send.path = self.ep_onemanage_fabric_group_details.path
            self.rest_send.verb = self.ep_onemanage_fabric_group_details.verb

            self.rest_send.save_settings()
            self.rest_send.check_mode = False
            self.rest_send.timeout = 1
            self.rest_send.commit()
            self.rest_send.restore_settings()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

        if not self.rest_send.response_current:
            msg = f"{self.class_name}.{method_name}: "
            msg += "self.rest_send.response_current is empty. "
            msg += "We should never hit this."
            self.log.debug(msg)
            raise ValueError(msg)
        if self.rest_send.response_current["DATA"] is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "DATA key is missing from response."
            self.log.debug(msg)
            raise ValueError(msg)

        self._build_data()

        try:
            self._register_result()
        except ValueError as error:
            raise ValueError(error) from error

        self.data_subclass = copy.deepcopy(self.data)
        self._refreshed = True

        msg = f"{self.class_name}.{method_name}: calling self.rest_send.commit() DONE"
        self.log.debug(msg)

    def _get(self, item):
        """
        Retrieve the value of the top-level (non-nvPair) item for fabric_group_name
        (anything not in the nvPairs dictionary).

        -   raise ``ValueError`` if ``fabric_group_name`` has not been set.
        -   raise ``ValueError`` if ``fabric_group_name`` does not exist
            on the controller.
        -   raise ``ValueError`` if item is not a valid property name for the fabric group.

        See also: ``_get_nv_pair()``
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.fabric_group_name {self.fabric_group_name} "
        self.log.debug(msg)

        if not self.fabric_group_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.fabric_group_name to a fabric group name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.fabric_group_name) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_group_name {self.fabric_group_name} does not exist on the controller."
            raise ValueError(msg)

        if self.data_subclass[self.fabric_group_name].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.fabric_group_name} unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(self.conversion.make_boolean(self.data_subclass[self.fabric_group_name].get(item)))

    def _get_nv_pair(self, item):
        """
        ### Summary
        Retrieve the value of the nvPair item for fabric_group_name.

        ### Raises
        - ``ValueError`` if:
                -   ``fabric_group_name`` has not been set.
                -   ``fabric_group_name`` does not exist on the controller.
                -   ``item`` is not a valid property name for the fabric.

        ### See also
        ``self._get()``
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.fabric_group_name {self.fabric_group_name} "
        self.log.debug(msg)

        if not self.fabric_group_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.fabric_group_name to a fabric group name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if not self.data_subclass.get(self.fabric_group_name):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_group_name {self.fabric_group_name} "
            msg += "does not exist on the controller."
            raise ValueError(msg)

        if self.data_subclass[self.fabric_group_name].get("nvPairs", {}).get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_group_name {self.fabric_group_name} "
            msg += f"unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(self.conversion.make_boolean(self.data_subclass[self.fabric_group_name].get("nvPairs").get(item)))

    @property
    def all_data(self) -> dict:
        """
        ### Summary
        Return all fabric details from the controller (i.e. self.data)

        ``refresh`` must be called before accessing this property.

        ### Raises
        None
        """
        return self.data

    @property
    def asn(self) -> str:
        """
        ### Summary
        Return the BGP asn of the fabric specified with filter, if it exists.
        Return "" (empty string) otherwise.

        This is an alias of bgp_as.

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "65000"
            - "" (empty string) if BGP_AS is not set
        """
        try:
            return self._get_nv_pair("BGP_AS") or ""
        except ValueError as error:
            msg = f"Failed to retrieve asn: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def bgp_as(self) -> str:
        """
        ### Summary
        Return ``nvPairs.BGP_AS`` of the fabric specified with filter, if it exists.
        Return "" (empty string) otherwise

        ### Raises
        None

        ### Type
        string

        ### Returns
            - e.g. "65000"
            - "" (empty string) if BGP_AS is not set
        """
        try:
            return self._get_nv_pair("BGP_AS") or ""
        except ValueError as error:
            msg = f"Failed to retrieve bgp_as: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def deployment_freeze(self) -> bool:
        """
        ### Summary
        The nvPairs.DEPLOYMENT_FREEZE of the fabric specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - False (if set to False, or not set)
        - True
        """
        try:
            return self._get_nv_pair("DEPLOYMENT_FREEZE") or False
        except ValueError as error:
            msg = f"Failed to retrieve deployment_freeze: Error detail: {error}"
            self.log.debug(msg)
            return False

    @property
    def enable_pbr(self) -> bool:
        """
        ### Summary
        The PBR enable state of the fabric specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - False (if set to False, or not set)
        - True
        """
        try:
            return self._get_nv_pair("ENABLE_PBR") or False
        except ValueError as error:
            msg = f"Failed to retrieve enable_pbr: Error detail: {error}"
            self.log.debug(msg)
            return False

    @property
    def fabric_group_name(self) -> str:
        """
        ### Summary
        The fabric group name to query.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. MyFabricGroup
        - "" (empty string) if fabric group name is not set
        """
        return self._fabric_group_name

    @fabric_group_name.setter
    def fabric_group_name(self, value: str) -> None:
        self.ep_onemanage_fabric_group_details.fabric_name = value
        self._fabric_group_name = value

    @property
    def fabric_id(self) -> str:
        """
        ### Summary
        The ``fabricId`` value of the fabric specified with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. FABRIC-5
        - "" if fabricId is not set
        """
        try:
            return self._get("fabricId") or ""
        except ValueError as error:
            msg = f"Failed to retrieve fabric_id: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def fabric_type(self) -> str:
        """
        ### Summary
        The ``nvPairs.FABRIC_TYPE`` value of the fabric specified with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - e.g. Switch_Fabric
        - "" (empty string) if FABRIC_TYPE is not set
        """
        try:
            return self._get_nv_pair("FABRIC_TYPE") or ""
        except ValueError as error:
            msg = f"Failed to retrieve fabric_type: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def is_read_only(self) -> bool:
        """
        ### Summary
        The ``nvPairs.IS_READ_ONLY`` value of the fabric specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - True
        - False (if set to False, or not set)
        """
        try:
            return self._get_nv_pair("IS_READ_ONLY") or False
        except ValueError as error:
            msg = f"Failed to retrieve is_read_only: Error detail: {error}"
            self.log.debug(msg)
            return False

    @property
    def per_vrf_loopback_auto_provision(self) -> bool:
        """
        ### Summary
        The ``nvPairs.PER_VRF_LOOPBACK_AUTO_PROVISION`` value of the fabric
        specified with filter.

        ### Raises
        None

        ### Type
        boolean

        ### Returns
        - True
        - False (if set to False, or not set)
        """
        try:
            return self._get_nv_pair("PER_VRF_LOOPBACK_AUTO_PROVISION") or False
        except ValueError as error:
            msg = "Failed to retrieve per_vrf_loopback_auto_provision: "
            msg += f"Error detail: {error}"
            self.log.debug(msg)
            return False

    @property
    def replication_mode(self) -> str:
        """
        ### Summary
        The ``nvPairs.REPLICATION_MODE`` value of the fabric specified
        with filter.

        ### Raises
        None

        ### Type
        string

        ### Returns
        - Ingress
        - Multicast
        - "" (empty string) if REPLICATION_MODE is not set
        """
        try:
            return self._get_nv_pair("REPLICATION_MODE") or ""
        except ValueError as error:
            msg = f"Failed to retrieve replication_mode: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def refreshed(self) -> bool:
        """
        Indicates whether the fabric group details have been refreshed.
        """
        return self._refreshed

    @property
    def template_name(self) -> str:
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
        - Empty string, if templateName is not set
        """
        try:
            return self._get("templateName") or ""
        except ValueError as error:
            msg = f"Failed to retrieve template_name: Error detail: {error}"
            self.log.debug(msg)
            return ""

    @property
    def filtered_data(self) -> dict:
        """
        ### Summary
        The DATA portion of the dictionary for the fabric group specified with fabric_group_name.

        ### Raises
        -   ``ValueError`` if:
                -   ``fabric_group_name`` has not been set.

        ### Returns
        - A dictionary of the fabric group matching fabric_group_name.
        - Empty dictionary, if the fabric group does not exist on the controller.
        """
        method_name = inspect.stack()[0][3]
        if not self.fabric_group_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.fabric_group_name must be set before accessing "
            msg += f"{self.class_name}.filtered_data."
            raise ValueError(msg)
        return self.data_subclass.get(self.fabric_group_name, {})

    @property
    def rest_send(self) -> RestSend:
        """
        An instance of the RestSend class.
        """
        if self._rest_send is None:
            msg = f"{self.class_name}.rest_send: "
            msg += "rest_send property should be set before accessing."
            raise ValueError(msg)
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        An instance of the Results class.
        """
        if self._results is None:
            msg = f"{self.class_name}.results: "
            msg += "results property should be set before accessing."
            raise ValueError(msg)
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        self._results = value
        self._results.action = self.action
        self._results.add_changed(False)
        self._results.operation_type = self.operation_type
