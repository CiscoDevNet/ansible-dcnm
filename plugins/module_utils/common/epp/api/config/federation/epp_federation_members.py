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

from .....api.config.federation.federation import \
    EpFederationMembers
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.ep.nexus.api.federation.v4.members.members import \
#     EpFederationMembers
from .....conversion import \
    ConversionUtils
from .....properties import \
    Properties


@Properties.add_rest_send
@Properties.add_results
class EppFederationMembers:
    """
    ### Summary
    Parent class for *FabricsVrfs() subclasses.
    See subclass docstrings for details.

    ### Raises
    None

    ### Data Structure
    ```json
    [
        {
            "clusterInfo": [
                {
                    "name": "ckab-nd321e",
                    "dataIP": "",
                    "mgmtIP": "172.22.150.244",
                    "mgmtIPv6": "",
                    "serial": "3F7CDCDE032B",
                    "currentState": "Active"
                }
            ],
            "fedUUID": "federation-nd1",
            "latitude": "",
            "local": true,
            "longitude": "",
            "manager": true,
            "memberHealth": "Up",
            "meta": {
                "modts": "2024-10-08T21:16:25.845451206Z",
                "createts": "2024-10-08T21:16:25.845451206Z",
                "dn": "fedmember/federation-nd1",
                "type": "fedmember",
                "version": 1
            },
            "name": "nd1",
            "schemaversion": "",
            "securityDomains": [],
            "version": "3.2.1e"
        }
    ]
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "federation_members"
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED EppFederationMembers()"
        self.log.debug(msg)

        self.data = {}
        self.conversion = ConversionUtils()
        self.ep_federation_members_list = EpFederationMembers()

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
            self.rest_send.path = self.ep_federation_members_list.path
            self.rest_send.verb = self.ep_federation_members_list.verb

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
        if self.result_code in [400, 401]:
            # TODO: Verify 400 response
            self._result_message = response_data.get("message")
            msg = f"Received result_code {self.result_code}. "
            msg += f"Message: {self._result_message}"
            self.log.debug(msg)
            self.data = {}
        elif self.result_code == 200:
            self.data = self.rest_send.response_current.get("DATA", {})
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

    def _get_cluster_info(self, item):
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


class EppFederationMemberByName(EppFederationMembers):
    """
    ### Summary
    Retrieve federation member details from the controller and provide
    property accessors for the federation member attributes.

    ### Raises
    -   ``ValueError`` if:
            -   ``super.__init__()`` raises ``ValueError``.
            -   ``refresh_super()`` raises ``ValueError``.
            -   ``refresh()`` raises ``ValueError``.
            -   ``filter`` is not set before accessing properties.
            -   ``federation_name`` does not exist on the controller.
            -   An attempt is made to access a key that does not exist
                for the filtered federation_name.

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.epp.api.config.federation import EppFederationMemberByName
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = EppFederationMemberByName()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    instance.name = "MyFederationMember"

    # all details for "MyFederationMember"
    details_dict = instance.filtered_data
    if details_dict is None:
        # federation member does not exist on the controller
    # etc...
    ```

    Or:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.epp.api.config.federation.epp_federation_members import EppFederationMemberByName
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = EppFederationMemberByName()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    all_federation_members = instance.all_data
    ```

    Where ``all_federation_members`` will be a dictionary of all federation_members
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        super().__init__()

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED EppFederationMemberByName()"
        self.log.debug(msg)

        self.data_subclass = {}
        self._name = None
        self._filter = None

    def refresh(self):
        """
        ### Refresh federation members current details from the controller

        ### Raises
        -   ``ValueError`` if:
                -   Mandatory properties are not set.
        """
        try:
            self.refresh_super()
        except ValueError as error:
            msg = "Failed to refresh federation member details: "
            msg += f"Error detail: {error}."
            raise ValueError(msg) from error

        # data_subclass is keyed on name
        self.data_subclass = dict()
        for item in self.data:
            name = item.get("name")
            if name is None:
                continue
            self.data_subclass[name] = copy.deepcopy(item)

    def _get(self, item):
        """
        Retrieve the value of top-level items.

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
            msg += "set instance.filter to a federation member name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"federation member name {self.filter} does not exist on the controller."
            raise ValueError(msg)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(self.data_subclass[self.filter].get(item))
        )

    def _get_cluster_info(self, item):
        """
        ### Summary
        Retrieve the value of the clusterInfo item for filter.

        ### Raises
        - ``ValueError`` if:
                -   ``self.filter`` has not been set.
                -   ``self.filter`` (federation cluster member name) does not exist on the controller.
                -   ``item`` is not a valid property name in clusterInfo.

        ### See also
        ``self._get()``
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.filter {self.filter} "
        self.log.debug(msg)

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a federation member name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"federation member name {self.filter} "
            msg += "does not exist on the controller."
            raise ValueError(msg)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"federation member name {self.filter} "
            msg += f"property name: {item} does not exist in clusterInfo."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(
                self.data_subclass[self.filter].get(item)
            )
        )

    @property
    def fed_uuid(self):
        return self._get("fedUUID")

    @property
    def latitude(self):
        return self._get("latitude")

    @property
    def longitude(self):
        return self._get("longitude")

    @property
    def manager(self):
        return self._get("manager")

    @property
    def member_health(self):
        return self._get("memberHealth")

    @property
    def schema_version(self):
        return self._get("schemaversion")

    @property
    def security_domains(self):
        return self._get("securityDomains")

    @property
    def version(self):
        return self._get("version")

    @property
    def name(self):
        return self._get("name")

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
        Set the federation member name to query.

        ### Raises
        None

        ### NOTES
        ``filter`` must be set before accessing this class's properties.
        """
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value
