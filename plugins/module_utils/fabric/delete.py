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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
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

    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.delete import \
        FabricDelete
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
        Results

    instance = FabricDelete(ansible_module)
    instance.fabric_names = ["FABRIC_1", "FABRIC_2"]
    instance.results = self.results
    instance.commit()
    results.build_final_result()

    # diff contains a dictionary of changes made
    diff = results.diff
    # result contains the result(s) of the delete request
    result = results.result
    # response contains the response(s) from the controller
    response = results.response

    # results.final_result contains all of the above info, and can be passed
    # to the exit_json and fail_json methods of AnsibleModule:

    if True in results.failed:
        msg = "Query failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__
        self.action = "delete"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._fabrics_to_delete = []
        self._build_properties()
        self._endpoints = ApiEndpoints()

        self._fabric_details = FabricDetailsByName(self.ansible_module)
        self._fabric_details.rest_send = RestSend(self.ansible_module)

        self._fabric_summary = FabricSummary(self.ansible_module)
        self._fabric_summary.rest_send = RestSend(self.ansible_module)

        self._cannot_delete_fabric_reason = None

        # path and verb cannot be defined here because endpoints.fabric name
        # must be set first.  Set these to None here and define them later in
        # the commit() method.
        self.path = None
        self.verb = None

        msg = "ENTERED FabricDelete(): "
        msg += f"action: {self.action}, "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # self.properties is already set in the parent class
        self.properties["fabric_names"] = None
        self.properties["rest_send"] = None

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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self._fabric_summary.fabric_name = fabric_name
        self._fabric_summary.refresh()
        if self._fabric_summary.fabric_is_empty is False:
            self._cannot_delete_fabric_reason = "Fabric is not empty"
            return False
        return True

    def _set_fabric_delete_endpoint(self, fabric_name) -> None:
        """
        - Set the fabric delete endpoint for fabric_name
        - Raise ``ValueError`` if the endpoint assignment fails
        """
        self._endpoints.fabric_name = fabric_name
        try:
            endpoint = self._endpoints.fabric_delete
        except ValueError as error:
            raise ValueError(f"{error}") from error
        self.path = endpoint.get("path")
        self.verb = endpoint.get("verb")

    def _validate_commit_parameters(self):
        """
        - validate the parameters for commit
        - raise ``ValueError`` if ``fabric_names`` is not set
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

        if self.fabric_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be set prior to calling commit."
            raise ValueError(msg)

    def commit(self):
        """
        - delete each of the fabrics in self.fabric_names
        - raise ``ValueError`` if any commit parameters are invalid
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self._validate_commit_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        self._get_fabrics_to_delete()

        msg = f"self._fabrics_to_delete: {self._fabrics_to_delete}"
        self.log.debug(msg)
        if len(self._fabrics_to_delete) != 0:
            self._send_requests()
        else:
            self.results.action = self.action
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.diff_current = {}
            self.results.result_current = {"success": True, "changed": False}
            msg = "No fabrics to delete"
            self.results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
            self.log.debug(msg)

    def _send_requests(self):
        """
        1.  Update RestSend() parameters:
            - check_mode : Enables or disables sending the request
            - timeout : Reduce to 1 second from default of 300 seconds
        2.  Call _send_request() for each fabric to be deleted.

        NOTES:
        -   We don't want RestSend to retry on errors since the likelihood of a
            timeout error when deleting a fabric is low, and there are cases of
            permanent errors for which we don't want to retry.  Hence, we set
            timeout to 1 second.
        """
        self.rest_send.check_mode = self.check_mode
        self.rest_send.timeout = 1

        for fabric_name in self._fabrics_to_delete:
            self._send_request(fabric_name)

    def _send_request(self, fabric_name):
        """
        Send a delete request to the controller and register the result.
        """
        method_name = inspect.stack()[0][3]

        try:
            self._set_fabric_delete_endpoint(fabric_name)
        except ValueError as error:
            raise ValueError(error) from error

        msg = f"{self.class_name}.{method_name}: "
        msg += f"verb: {self.verb}, path: {self.path}"
        self.log.debug(msg)

        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.commit()
        self.register_result(fabric_name)

    def register_result(self, fabric_name):
        """
        Register the result of the fabric create request
        """
        if self.rest_send.result_current["success"]:
            self.results.diff_current = {"fabric_name": fabric_name}
            # need this to match the else clause below since we
            # pass response_current (altered or not) to the results object
            response_current = copy.deepcopy(self.rest_send.response_current)
        else:
            self.results.diff_current = {}
            # Improve the controller's error message to include the fabric_name
            response_current = copy.deepcopy(self.rest_send.response_current)
            if "DATA" in response_current:
                if "Failed to delete the fabric." in response_current["DATA"]:
                    msg = f"Failed to delete fabric {fabric_name}."
                    response_current["DATA"] = msg

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state
        self.results.response_current = response_current
        self.results.result_current = self.rest_send.result_current

        self.results.register_task_result()

    @property
    def fabric_names(self):
        """
        - getter: return list of fabric_names
        - setter: set list of fabric_names
        - setter: raise ``ValueError`` if ``value`` is not a ``list`` of ``str``
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
            raise ValueError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be a list of at least one string. "
            msg += f"got {value}."
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "fabric_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                raise ValueError(msg)
        self.properties["fabric_names"] = value

    @property
    def rest_send(self):
        """
        An instance of the RestSend class.
        """
        return self.properties["rest_send"]

    @rest_send.setter
    def rest_send(self, value):
        self.properties["rest_send"] = value
