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
import json
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints


class FabricCreateCommon(FabricCommon):
    """
    Common methods and properties for:
    - FabricCreate
    - FabricCreateBulk
    """

    def __init__(self, params):
        super().__init__(params)
        self.class_name = self.__class__.__name__
        self.action: str = "create"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.endpoints = ApiEndpoints()

        # path and verb cannot be defined here because endpoints.fabric name
        # must be set first.  Set these to None here and define them later in
        # the commit() method.
        self.path: str = None
        self.verb: str = None

        self._payloads_to_commit: list = []

        self._mandatory_payload_keys = set()
        self._mandatory_payload_keys.add("FABRIC_NAME")
        self._mandatory_payload_keys.add("BGP_AS")

        self._build_properties()

        msg = "ENTERED FabricCreateCommon(): "
        msg += f"action: {self.action}, "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

    def _build_properties(self):
        """
        - Add properties specific to this class
        - self._properties is initialized in FabricCommon
        """
        pass

    def _verify_payload(self, payload) -> None:
        """
        - Verify that the payload is a dict and contains all mandatory keys
        - raise ``ValueError`` if the payload is not a dict
        - raise ``ValueError`` if the payload is missing mandatory keys
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"payload: {payload}"
        self.log.debug(msg)

        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dict. "
            msg += f"Got type {type(payload).__name__}, "
            msg += f"value {payload}"
            raise ValueError(msg)

        missing_keys = []
        for key in self._mandatory_payload_keys:
            if key not in payload:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += "payload is missing mandatory keys: "
        msg += f"{sorted(missing_keys)}"
        msg += f"payload: {sorted(payload)}"
        raise ValueError(msg)

    def _build_payloads_to_commit(self) -> None:
        """
        Build a list of payloads to commit.  Skip any payloads that
        already exist on the controller.

        Expects self.payloads to be a list of dict, with each dict
        being a payload for the fabric create API endpoint.

        Populates self._payloads_to_commit with a list of payloads
        to commit.
        """
        self.fabric_details.refresh()

        self._payloads_to_commit = []
        for payload in self.payloads:
            if payload.get("FABRIC_NAME", None) in self.fabric_details.all_data:
                continue
            self._payloads_to_commit.append(copy.deepcopy(payload))

    def _set_fabric_create_endpoint(self, payload):
        """
        - Set the endpoint for the fabric create API call.
        - raise ``ValueError`` if FABRIC_TYPE in the payload is invalid
        - raise ``ValueError`` if the fabric_type to template_name mapping fails
        - raise ``ValueError`` if the fabric_create endpoint assignment fails
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.endpoints.fabric_name = payload.get("FABRIC_NAME")

        try:
            self.fabric_type = copy.copy(payload.get("FABRIC_TYPE"))
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            template_name = self.fabric_type_to_template_name(self.fabric_type)
        except ValueError as error:
            raise ValueError(f"{error}") from error
        self.endpoints.template_name = template_name

        try:
            endpoint = self.endpoints.fabric_create
        except ValueError as error:
            raise ValueError(f"{error}") from error

        payload.pop("FABRIC_TYPE", None)
        self.path = endpoint["path"]
        self.verb = endpoint["verb"]

    def _send_payloads(self):
        """
        -   If ``check_mode`` is ``False``, send the payloads
            to the controller
        -   If ``check_mode`` is ``True``, do not send the payloads
            to the controller
        -   In both cases, register results
        -   raise ``ValueError`` if the fabric_create endpoint assignment fails
        """
        self.rest_send.check_mode = self.check_mode

        for payload in self._payloads_to_commit:
            try:
                self._set_fabric_create_endpoint(payload)
            except ValueError as error:
                raise ValueError(f"{error}") from error

            # For FabricUpdate, the DEPLOY key is mandatory.
            # For FabricCreate, it is not.
            # Remove it if it exists.
            payload.pop("DEPLOY", None)

            # We don't want RestSend to retry on errors since the likelihood of a
            # timeout error when creating a fabric is low, and there are many cases
            # of permanent errors for which we don't want to retry.
            self.rest_send.timeout = 1

            self.rest_send.path = self.path
            self.rest_send.verb = self.verb
            self.rest_send.payload = payload
            self.rest_send.commit()

            if self.rest_send.result_current["success"] is False:
                self.results.diff_current = {}
            else:
                self.results.diff_current = copy.deepcopy(payload)
            self.results.action = self.action
            self.results.state = self.state
            self.results.check_mode = self.check_mode
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

            msg = f"self.results.diff: {json.dumps(self.results.diff, indent=4, sort_keys=True)}"
            self.log.debug(msg)

    @property
    def payloads(self):
        """
        Payloads must be a ``list`` of ``dict`` of payloads for the
        ``fabric_create`` endpoint.

        - getter: Return the fabric create payloads
        - setter: Set the fabric create payloads
        - setter: raise ``ValueError`` if ``payloads`` is not a ``list`` of ``dict``
        - setter: raise ``ValueError`` if any payload is missing mandatory keys
        """
        return self._properties["payloads"]

    @payloads.setter
    def payloads(self, value):
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"value: {value}"
        self.log.debug(msg)

        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise ValueError(msg)
        for item in value:
            try:
                self._verify_payload(item)
            except ValueError as error:
                raise ValueError(f"{error}") from error
        self._properties["payloads"] = value


class FabricCreateBulk(FabricCreateCommon):
    """
    Create fabrics in bulk.  Skip any fabrics that already exist.

    Usage:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.create import \
        FabricCreateBulk
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
        Results

    payloads = [ 
        { "FABRIC_NAME": "fabric1", "BGP_AS": 65000 },
        { "FABRIC_NAME": "fabric2", "BGP_AS": 65001 }
    ]
    results = Results()
    instance = FabricCreateBulk(ansible_module)
    instance.rest_send = RestSend(ansible_module)
    instance.payloads = payloads
    instance.results = results
    instance.commit()
    results.build_final_result()

    # diff contains a dictionary of payloads that succeeded and/or failed
    diff = results.diff
    # result contains the result(s) of the fabric create request
    result = results.result
    # response contains the response(s) from the controller
    response = results.response

    # results.final_result contains all of the above info, and can be passed
    # to the exit_json and fail_json methods of AnsibleModule:

    if True in results.failed:
        msg = "Fabric create failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)
    ```
    """

    def __init__(self, params):
        super().__init__(params)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricCreateBulk()")

        self._build_properties()

    def _build_properties(self):
        """
        Add properties specific to this class
        """
        # properties dict is already initialized in the parent class
        self._properties["payloads"] = None

    def commit(self):
        """
        # create fabrics.

        - Skip any fabrics that already exist on the controller.
        - raise ``ValueError`` if ``payloads`` is not set.
        - raise ``ValueError`` if payload fixup fails.
        - raise ``ValueError`` if sending the payloads fails.
        """
        method_name = inspect.stack()[0][3]
        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            raise ValueError(msg)

        self._build_payloads_to_commit()

        msg = "self._payloads_to_commit: "
        msg += f"{json.dumps(self._payloads_to_commit, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if len(self._payloads_to_commit) == 0:
            return
        try:
            self._fixup_payloads_to_commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            self._send_payloads()
        except ValueError as error:
            raise ValueError(f"{error}") from error


class FabricCreate(FabricCreateCommon):
    """
    Create a VXLAN fabric on the controller and register the result.

    NOTES:
    -   FabricCreateBulk is used currently.
    -   FabricCreate may be useful in the future, but is not currently used
        and could be deleted if not needed.
    """

    def __init__(self, params):
        super().__init__(params)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricCreate()")

        self.endpoints = ApiEndpoints()

        self._init_properties()

    def _init_properties(self):
        """
        Add properties specific to this class
        """
        # self._properties is already initialized in the parent class
        self._properties["payload"] = None

    def commit(self):
        """
        -   Send the fabric create request to the controller.
        -   Register the result of the fabric create request.
        -   raise ``ValueError`` if ``rest_send`` is not set.
        -   raise ``ValueError`` if ``payload`` is not set.
        -   raise ``ValueError`` if ``fabric_create`` endpoint
            assignment fails.
        -   return if ``payload`` is empty.
        """
        method_name = inspect.stack()[0][3]
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit. "
            raise ValueError(msg)

        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be set prior to calling commit. "
            raise ValueError(msg)

        # TODO: Review this.
        if len(self.payload) == 0:
            return

        try:
            self._set_fabric_create_endpoint(self.payload)
        except ValueError as error:
            raise ValueError(f"{error}") from error

        self.rest_send.check_mode = self.check_mode
        self.rest_send.timeout = 1
        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.payload = self.payload
        self.rest_send.commit()

        self.register_result()

    def register_result(self):
        """
        Register the result of the fabric create request
        """
        if self.rest_send.result_current["success"]:
            self.results.diff_current = self.payload
        else:
            self.results.diff_current = {}

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state
        self.results.result_current = self.rest_send.result_current
        self.results.response_current = self.rest_send.response_current
        self.results.register_task_result()

    @property
    def payload(self):
        """
        Return a fabric create payload.
        """
        return self._properties["payload"]

    @payload.setter
    def payload(self, value):
        self._properties["payload"] = value
