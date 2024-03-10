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

from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_fabric import \
    RestSend


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
        self._rest_send = RestSend(self.ansible_module)

        # path and verb cannot be defined here because endpoints.fabric name
        # must be set first.  Set these to None here and define them later in
        # the commit() method.
        self.path = None
        self.verb = None

        self.action = "delete"
        self.changed = False
        self.failed = False

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
        msg = f"self._fabric_summary.fabric_is_empty: "
        msg += f"fabric_is_empty: {self._fabric_summary.fabric_is_empty}"
        self.log.debug(msg)
        if self._fabric_summary.fabric_is_empty is False:
            self.cannot_delete_fabric_reason = "Fabric is not empty"
            return False
        return True

    def _set_endpoint(self, fabric_name):
        """
        return the endpoint for the fabric_name
        """
        self._endpoints.fabric_name = fabric_name
        try:
            self._endpoint = self._endpoints.fabric_delete
        except ValueError as error:
            self.ansible_module.fail_json(error, **self.failed_result)
        self.path = self._endpoint.get("path")
        self.verb = self._endpoint.get("verb")

    def commit(self):
        """
        delete each of the fabrics in self.fabric_names
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.failed_result)

        self._get_fabrics_to_delete()

        msg = f"self._fabrics_to_delete: {self._fabrics_to_delete}"
        self.log.debug(msg)
        if len(self._fabrics_to_delete) == 0:
            self.changed = False
            self.failed = False
            return

        msg = f"Populating diff {self._fabrics_to_delete}"
        self.log.debug(msg)

        for fabric_name in self._fabrics_to_delete:
            if self._can_fabric_be_deleted(fabric_name) is False:
                msg = f"Cannot delete fabric {fabric_name}. "
                msg += f"Reason: {self.cannot_delete_fabric_reason}"
                self.ansible_module.fail_json(msg, **self.failed_result)

            self._set_endpoint(fabric_name)
            self._rest_send.path = self.path
            self._rest_send.verb = self.verb
            self._rest_send.commit()

            self.diff = {"fabric_name": fabric_name}
            self.response = copy.deepcopy(self._rest_send.response_current)
            self.response_current = copy.deepcopy(self._rest_send.response_current)
            self.result = copy.deepcopy(self._rest_send.result_current)
            self.result_current = copy.deepcopy(self._rest_send.result_current)

        # msg = f"self.diff: {self.diff}"
        # self.log.debug(msg)
        msg = f"self.response: {self.response}"
        self.log.debug(msg)
        msg = f"self.result: {self.result}"
        self.log.debug(msg)
        msg = f"self.response_current: {self.response_current}"
        self.log.debug(msg)
        msg = f"self.result_current: {self.result_current}"
        self.log.debug(msg)
