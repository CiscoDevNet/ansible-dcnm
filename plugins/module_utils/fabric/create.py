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

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.check_mode = self.ansible_module.check_mode
        msg = "ENTERED FabricCreateCommon(): "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.fabric_details = FabricDetailsByName(self.ansible_module)
        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)
        self._verify_params = VerifyPlaybookParams(self.ansible_module)

        # path and verb cannot be defined here because endpoints.fabric name
        # must be set first.  Set these to None here and define them later in
        # the commit() method.
        self.path = None
        self.verb = None

        self.action = "create"
        self._payloads_to_commit = []
        self.response_ok = []
        self.result_ok = []
        self.diff_ok = []
        self.response_nok = []
        self.result_nok = []
        self.diff_nok = []

        self._mandatory_payload_keys = set()
        self._mandatory_payload_keys.add("FABRIC_NAME")
        self._mandatory_payload_keys.add("BGP_AS")

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
            self.ansible_module.fail_json(msg, **self.failed_result)

        missing_keys = []
        for key in self._mandatory_payload_keys:
            if key not in payload:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += "payload is missing mandatory keys: "
        msg += f"{sorted(missing_keys)}"
        self.ansible_module.fail_json(msg, **self.failed_result)

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

        In both cases, populate the following lists:

        - self.response_ok  : list of controller responses associated with success result
        - self.result_ok    : list of results where success is True
        - self.diff_ok      : list of payloads for which the request succeeded
        - self.response_nok : list of controller responses associated with failed result
        - self.result_nok   : list of results where success is False
        - self.diff_nok     : list of payloads for which the request failed
        """
        self.rest_send.check_mode = self.check_mode

        self.response_ok = []
        self.result_ok = []
        self.diff_ok = []
        self.response_nok = []
        self.result_nok = []
        self.diff_nok = []
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

            if self.rest_send.result_current["success"]:
                self.response_ok.append(copy.deepcopy(self.rest_send.response_current))
                self.result_ok.append(copy.deepcopy(self.rest_send.result_current))
                self.diff_ok.append(copy.deepcopy(payload))
            else:
                self.response_nok.append(copy.deepcopy(self.rest_send.response_current))
                self.result_nok.append(copy.deepcopy(self.rest_send.result_current))
                self.diff_nok.append(copy.deepcopy(payload))

    def _process_responses(self):
        method_name = inspect.stack()[0][3]

        # All requests succeeded, set changed to True and return
        if len(self.result_nok) == 0:
            self.changed = True
            for diff in self.diff_ok:
                diff["action"] = self.action
                self.diff = copy.deepcopy(diff)
            for result in self.result_ok:
                self.result = copy.deepcopy(result)
                self.result_current = copy.deepcopy(result)
            for response in self.response_ok:
                self.response = copy.deepcopy(response)
                self.response_current = copy.deepcopy(response)
            return

        self.failed = True
        self.changed = False
        # at least one request succeeded, so set changed to True
        if len(self.result_nok) != len(self._payloads_to_commit):
            self.changed = True

        # Provide the info for the request(s) that succeeded
        # and the request(s) that failed

        # Add an "OK" result to the response(s) that succeeded
        for diff in self.diff_ok:
            diff["action"] = self.action
            diff["result"] = "OK"
            self.diff = copy.deepcopy(diff)
        for result in self.result_ok:
            result["result"] = "OK"
            self.result = copy.deepcopy(result)
            self.result_current = copy.deepcopy(result)
        for response in self.response_ok:
            response["result"] = "OK"
            self.response = copy.deepcopy(response)
            self.response_current = copy.deepcopy(response)

        # Add a "FAILED" result to the response(s) that failed
        for diff in self.diff_nok:
            diff["action"] = self.action
            diff["result"] = "FAILED"
            self.diff = copy.deepcopy(diff)
        for result in self.result_nok:
            result["result"] = "FAILED"
            self.result = copy.deepcopy(result)
            self.result_current = copy.deepcopy(result)
        for response in self.response_nok:
            response["result"] = "FAILED"
            self.response = copy.deepcopy(response)
            self.response_current = copy.deepcopy(response)

        result = {}
        result["diff"] = {}
        result["response"] = {}
        result["result"] = {}
        result["failed"] = self.failed
        result["changed"] = self.changed
        result["diff"]["OK"] = self.diff_ok
        result["response"]["OK"] = self.response_ok
        result["result"]["OK"] = self.result_ok
        result["diff"]["FAILED"] = self.diff_nok
        result["response"]["FAILED"] = self.response_nok
        result["result"]["FAILED"] = self.result_nok

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Bad response(s) during fabric {self.action}. "
        self.ansible_module.fail_json(msg, **result)

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
            self.ansible_module.fail_json(msg, **self.failed_result)
        for item in value:
            self._verify_payload(item)
        self.properties["payloads"] = value


class FabricCreateBulk(FabricCreateCommon):
    """
    Create fabrics in bulk.  Skip any fabrics that already exist.
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
            self.ansible_module.fail_json(msg, **self.failed_result)

        self._build_payloads_to_commit()
        if len(self._payloads_to_commit) == 0:
            return
        self._fixup_payloads_to_commit()
        self._send_payloads()
        self._process_responses()


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
            self.ansible_module.fail_json(msg)

        if len(self.payload) == 0:
            self.ansible_module.exit_json(**self.failed_result)

        fabric_name = self.payload.get("FABRIC_NAME")
        if fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload is missing mandatory FABRIC_NAME key."
            self.ansible_module.fail_json(msg)

        self.endpoints.fabric_name = fabric_name
        self.endpoints.template_name = "Easy_Fabric"
        try:
            endpoint = self.endpoints.fabric_create
        except ValueError as error:
            self.ansible_module.fail_json(error)

        path = endpoint["path"]
        verb = endpoint["verb"]

        self.rest_send.path = path
        self.rest_send.verb = verb
        self.rest_send.payload = self.payload
        self.rest_send.commit()

        self.result_current = self.rest_send.result_current
        self.result = self.rest_send.result_current
        self.response_current = self.rest_send.response_current
        self.response = self.rest_send.response_current

        if self.response_current["RETURN_CODE"] == 200:
            self.diff = self.payload

    @property
    def payload(self):
        """
        Return a fabric create payload.
        """
        return self.properties["payload"]

    @payload.setter
    def payload(self, value):
        self.properties["payload"] = value