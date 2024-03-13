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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_fabric import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary


class FabricDelete(FabricCommon):
    """
    Delete fabrics

    A fabric must be empty before it can be deleted.

    Usage:

    instance = FabricDelete(ansible_module)
    instance.fabric_names = ["FABRIC_1", "FABRIC_2"]
    instance.commit()
    diff = instance.diff # contains list of deleted fabrics
    result = instance.result # contains the result(s) of the delete request
    response = instance.response # contains the response(s) from the controller
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED FabricDelete(): "
        msg += f"state: {self.state}"
        self.log.debug(msg)

        self._fabrics_to_delete = []
        self._build_properties()
        self._endpoints = ApiEndpoints()
        self._fabric_details = FabricDetailsByName(self.ansible_module)
        self._fabric_summary = FabricSummary(self.ansible_module)
        self.rest_send = RestSend(self.ansible_module)

        self._cannot_delete_fabric_reason = None

        # path and verb cannot be defined here because endpoints.fabric name
        # must be set first.  Set these to None here and define them later in
        # the commit() method.
        self.path = None
        self.verb = None

        self.action = "delete"
        self.changed = False
        self.failed = False
        self.response_ok = []
        self.result_ok = []
        self.diff_ok = []
        self.response_nok = []
        self.result_nok = []
        self.diff_nok = []

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # self.properties is already set in the parent class
        self.properties["fabric_names"] = None

    @property
    def fabric_names(self):
        """
        return the fabric names
        """
        return self.properties["fabric_names"]

    @fabric_names.setter
    def fabric_names(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be a list of at least one string. "
            msg += f"got {value}."
            self.ansible_module.fail_json(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "fabric_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                self.ansible_module.fail_json(msg)
        self.properties["fabric_names"] = value

    def _get_fabrics_to_delete(self) -> None:
        """
        Retrieve fabric info from the controller and set the list of
        controller fabrics that are in our fabric_names list.
        """
        self._fabric_details.refresh()

        self._fabrics_to_delete = []
        for fabric_name in self.fabric_names:
            if fabric_name in self._fabric_details.all_data:
                self._fabrics_to_delete.append(fabric_name)

    def _can_fabric_be_deleted(self, fabric_name):
        """
        return True if the fabric can be deleted
        return False otherwise
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "ENTERED"
        self.log.debug(msg)
        self._fabric_summary.fabric_name = fabric_name
        self._fabric_summary.refresh()
        if self._fabric_summary.fabric_is_empty is False:
            self._cannot_delete_fabric_reason = "Fabric is not empty"
            return False
        return True

    def _set_fabric_delete_endpoint(self, fabric_name):
        """
        return the endpoint for the fabric_name
        """
        self._endpoints.fabric_name = fabric_name
        try:
            endpoint = self._endpoints.fabric_delete
        except ValueError as error:
            self.ansible_module.fail_json(error, **self.failed_result)
        self.path = endpoint.get("path")
        self.verb = endpoint.get("verb")

    def _validate_commit_parameters(self):
        """
        validate the parameters for commit
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.failed_result)

    def commit(self):
        """
        delete each of the fabrics in self.fabric_names
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self._validate_commit_parameters()

        self._get_fabrics_to_delete()

        msg = f"self._fabrics_to_delete: {self._fabrics_to_delete}"
        self.log.debug(msg)
        if len(self._fabrics_to_delete) == 0:
            self.changed = False
            self.failed = False
            return

        self._send_requests()
        self._process_responses()

    def _send_requests(self):
        """
        If check_mode is False, send the requests to the controller
        If check_mode is True, do not send the requests to the controller

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

        # We don't want RestSend to retry on errors since the likelihood of a
        # timeout error when deleting a fabric is low, and there are cases
        # of permanent errors for which we don't want to retry.
        self.rest_send.timeout = 1

        for fabric_name in self._fabrics_to_delete:
            self._send_request(fabric_name)

    def _send_request(self, fabric_name):
        method_name = inspect.stack()[0][3]
        self._set_fabric_delete_endpoint(fabric_name)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"verb: {self.verb}, path: {self.path}"
        self.log.debug(msg)

        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.commit()

        if self.rest_send.result_current["success"]:
            self.response_ok.append(copy.deepcopy(self.rest_send.response_current))
            self.result_ok.append(copy.deepcopy(self.rest_send.result_current))
            self.diff_ok.append({"fabric_name": fabric_name})
        else:
            # Improve the controller's error message to include the fabric_name
            response_current = copy.deepcopy(self.rest_send.response_current)
            if "DATA" in response_current:
                if "Failed to delete the fabric." in response_current["DATA"]:
                    msg = f"Failed to delete fabric {fabric_name}."
                    response_current["DATA"] = msg
            self.response_nok.append(copy.deepcopy(response_current))
            self.result_nok.append(copy.deepcopy(self.rest_send.result_current))
            self.diff_nok.append({"fabric_name": fabric_name})

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

        # At least one request failed.
        # Set failed to true, set changed appropriately,
        # build response/result/diff, and call fail_json
        self.failed = True
        self.changed = False
        # At least one request succeeded, so set changed to True
        if self.result_ok != 0:
            self.changed = True

        # Provide the results for all (failed and successful) requests

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
        msg += f"result: {json.dumps(result, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Bad response(s) during fabric {self.action}. "
        self.ansible_module.fail_json(msg, **result)
