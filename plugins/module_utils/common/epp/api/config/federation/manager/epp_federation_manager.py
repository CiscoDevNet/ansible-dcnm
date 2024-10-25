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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.config.federation.manager.manager import \
    EpFederationManagerGet
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.ep.nexus.api.federation.v4.members.members import \
#     EpFederationMembers
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties


@Properties.add_rest_send
@Properties.add_results
class EppFederationManagerGet:
    """
    ### Summary
    Retrieve federation manager details from the controller and provide
    property accessors for the federation manager attributes.

    ### Raises
    -   ``ValueError`` if:
            -   ``__init__()`` raises ``ValueError``.
            -   ``refresh()`` raises ``ValueError``.
            -   An attempt is made to access a key that does not exist
                for the federation manager.

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.epp.api.config.federation.manager.epp_federation_manager import \
        EppFederationManagerGet
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = EppFederationManagerGet()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()

    # details for the federation manager
    details_dict = instance.data
    # etc...
    ```

    ### Data Structure
    ```json
    {
        "fedUUID": "federation-nd1",
        "federationName": "federation-nd1",
        "force": false,
        "meta": {
            "modts": "2024-10-08T21:16:25.897891448Z",
            "createts": "2024-10-08T21:16:25.897891448Z",
            "dn": "ndsitefedmgr",
            "type": "ndsitefedmgr",
            "version": 1
        },
        "schemaversion": "",
        "securityDomains": []
    }
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "federation_manager"
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED EppFederationManagerGet()"
        self.log.debug(msg)

        self.data = {}
        self.conversion = ConversionUtils()
        self.ep_federation_manager = EpFederationManagerGet()

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

    def refresh(self):
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
            self.rest_send.path = self.ep_federation_manager.path
            self.rest_send.verb = self.ep_federation_manager.verb

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
        Retrieve the value of top-level items in the response DATA

        -   raise ``ValueError`` if ``self.filter`` has not been set.
        -   raise ``ValueError`` if ``self.filter`` (fabric_name) does not exist
            on the controller.
        -   raise ``ValueError`` if item is not a valid property name for the fabric.

        See also: ``_get_meta()``
        """
        method_name = inspect.stack()[0][3]

        if self.data.get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(self.data.get(item))
        )

    def _get_meta(self, item):
        """
        ### Summary
        Retrieve the value of the meta dictionary property matching item.

        ### Raises
        - ``ValueError`` if:
                -   ``self.filter`` has not been set.
                -   ``self.filter`` (federation cluster member name) does not exist on the controller.
                -   ``item`` is not a valid property name in clusterInfo.

        ### See also
        ``self._get()``
        """
        method_name = inspect.stack()[0][3]

        if self.data.get("meta") is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "controller response does not contain DATA.meta object."
            raise ValueError(msg)

        if self.data.get("meta", {}).get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"property name: {item} does not exist in DATA.meta object."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(
                self.data.get("meta", {}).get(item)
            )
        )

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

    @property
    def fed_uuid(self):
        return self._get("fedUUID")

    @property
    def federation_name(self):
        return self._get("federationName")

    @property
    def force(self):
        return self._get("force")

    @property
    def schema_version(self):
        return self._get("schemaversion")

    @property
    def security_domains(self):
        return self._get("securityDomains")

    @property
    def meta_created_timestamp(self):
        return self._get_meta("createts")

    @property
    def meta_dn(self):
        return self._get_meta("dn")

    @property
    def meta_modified_timestamp(self):
        return self._get_meta("modts")

    @property
    def meta_type(self):
        return self._get_meta("type")

    @property
    def meta_version(self):
        return self._get_meta("version")
