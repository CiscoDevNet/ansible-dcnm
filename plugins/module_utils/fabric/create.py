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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_fabric import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.vxlan.verify_playbook_params import \
    VerifyPlaybookParams


class FabricCreateCommon(FabricCommon):
    """
    Common methods and properties for:
    - FabricCreate
    - FabricCreateBulk
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__
        self.action = "create"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED FabricCreateCommon(): "
        msg += f"action: {self.action}, "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

        self.fabric_details = FabricDetailsByName(self.ansible_module)
        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)
        #self._verify_params = VerifyPlaybookParams(self.ansible_module)

        # path and verb cannot be defined here because endpoints.fabric name
        # must be set first.  Set these to None here and define them later in
        # the commit() method.
        self.path = None
        self.verb = None

        self._payloads_to_commit = []

        self._mandatory_payload_keys = set()
        self._mandatory_payload_keys.add("FABRIC_NAME")
        self._mandatory_payload_keys.add("BGP_AS")

        msg = "ENTERED FabricCreateCommon(): "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

    def _verify_payload(self, payload):
        """
        Verify that the payload is a dict and contains all mandatory keys
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dict. "
            msg += f"Got type {type(payload).__name__}, "
            msg += f"value {payload}"
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        missing_keys = []
        for key in self._mandatory_payload_keys:
            if key not in payload:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += "payload is missing mandatory keys: "
        msg += f"{sorted(missing_keys)}"
        self.ansible_module.fail_json(msg, **self.results.failed_result)

    def _fixup_payloads_to_commit(self):
        """
        Make any modifications to the payloads prior to sending them
        to the controller.

        Add any modifications to the list below.

        - Translate ANYCAST_GW_MAC to a format the controller understands
        """
        for payload in self._payloads_to_commit:
            if "ANYCAST_GW_MAC" in payload:
                payload["ANYCAST_GW_MAC"] = self.translate_mac_address(
                    payload["ANYCAST_GW_MAC"]
                )

    def _build_payloads_to_commit(self):
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

    def _get_endpoint(self):
        """
        Get the endpoint for the fabric create API call.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.endpoints.fabric_name = self._payloads_to_commit[0].get("FABRIC_NAME")
        self.endpoints.template_name = "Easy_Fabric"
        try:
            endpoint = self.endpoints.fabric_create
        except ValueError as error:
            self.ansible_module.fail_json(error)

        self.path = endpoint["path"]
        self.verb = endpoint["verb"]

    def _set_fabric_create_endpoint(self, payload):
        """
        Set the endpoint for the fabric create API call.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.endpoints.fabric_name = payload.get("FABRIC_NAME")
        self.fabric_type = copy.copy(payload.get("FABRIC_TYPE"))
        self.endpoints.template_name = self.fabric_type_to_template_name(
            self.fabric_type
        )
        try:
            endpoint = self.endpoints.fabric_create
        except ValueError as error:
            self.ansible_module.fail_json(error)

        payload.pop("FABRIC_TYPE", None)
        self.path = endpoint["path"]
        self.verb = endpoint["verb"]

    def _send_payloads(self):
        """
        If check_mode is False, send the payloads to the controller
        If check_mode is True, do not send the payloads to the controller

        In both cases, update results
        """
        self.rest_send.check_mode = self.check_mode

        for payload in self._payloads_to_commit:
            self._set_fabric_create_endpoint(payload)

            # For FabricUpdate, the DEPLOY key is mandatory.
            # For FabricCreate, it is not.
            # Remove it if it exists.
            payload.pop("DEPLOY", None)

            # We don't want RestSend to retry on errors since the likelihood of a
            # timeout error when updating a fabric is low, and there are many cases
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
            self.results.response_current = copy.deepcopy(self.rest_send.response_current)
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

    @property
    def payloads(self):
        """
        Return the fabric create payloads

        Payloads must be a list of dict. Each dict is a
        payload for the fabric create API endpoint.
        """
        return self.properties["payloads"]

    @payloads.setter
    def payloads(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg, **self.results.failed_result)
        for item in value:
            self._verify_payload(item)
        self.properties["payloads"] = value


class FabricCreateBulk(FabricCreateCommon):
    """
    Create fabrics in bulk.  Skip any fabrics that already exist.

    Usage:
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
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricCreateBulk()")

        self._build_properties()

    def _build_properties(self):
        """
        Add properties specific to this class
        """
        # properties dict is already initialized in the parent class
        self.properties["payloads"] = None

    def commit(self):
        """
        create fabrics.  Skip any fabrics that already exist
        on the controller,
        """
        method_name = inspect.stack()[0][3]
        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        self._build_payloads_to_commit()
        if len(self._payloads_to_commit) == 0:
            return
        self._fixup_payloads_to_commit()
        self._send_payloads()

class FabricCreate(FabricCommon):
    """
    Create a VXLAN fabric on the controller.
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricCreate()")

        self.data = {}
        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)

        self._init_properties()

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        self.properties["payload"] = None

    def commit(self):
        """
        Send the fabric create request to the controller.
        """
        method_name = inspect.stack()[0][3]
        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Exiting. Missing mandatory property: payload"
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        if len(self.payload) == 0:
            self.ansible_module.exit_json(**self.results.failed_result)

        fabric_name = self.payload.get("FABRIC_NAME")
        if fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload is missing mandatory FABRIC_NAME key."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        self.endpoints.fabric_name = fabric_name
        self.endpoints.template_name = "Easy_Fabric"
        try:
            endpoint = self.endpoints.fabric_create
        except ValueError as error:
            self.ansible_module.fail_json(error, **self.results.failed_result)

        path = endpoint["path"]
        verb = endpoint["verb"]

        self.rest_send.path = path
        self.rest_send.verb = verb
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
        return self.properties["payload"]

    @payload.setter
    def payload(self, value):
        self.properties["payload"] = value
