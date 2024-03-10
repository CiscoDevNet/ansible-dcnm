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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_fabric import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints


class FabricSummary(FabricCommon):
    """
    Return populate self.data with fabric summary information,
    formatted as a dictionary.

    Convenience properties are provided to access the data, including:
    @device_count
    @leaf_count
    @spine_count
    @border_gateway_count
    @in_sync_count
    @out_of_sync_count

    self.data will contain the following structure.

    {
        "switchSWVersions": {
            "10.2(5)": 7,
            "10.3(1)": 2
        },
        "switchHealth": {
            "Healthy": 2,
            "Minor": 7
        },
        "switchHWVersions": {
            "N9K-C93180YC-EX": 4,
            "N9K-C9504": 5
        },
        "switchConfig": {
            "Out-of-Sync": 5,
            "In-Sync": 4
        },
        "switchRoles": {
            "leaf": 4,
            "spine": 3,
            "border gateway": 2
        }
    }

    Usage:

    instance = FabricSummary(ansible_module)
    instance.fabric_name = "MyFabric"
    instance.refresh()
    fabric_summary = instance.data
    device_count = instance.device_count
    etc...
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED FabricSummary(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.data = None
        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)

        self._init_properties()

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        self.properties["border_gateway_count"] = 0
        self.properties["device_count"] = 0
        self.properties["fabric_name"] = None
        self.properties["leaf_count"] = 0
        self.properties["spine_count"] = 0

    def _update_device_counts(self):
        """
        Get the device counts from the controller.
        """
        method_name = inspect.stack()[0][3]
        if self.data is None:
            self.fail(f"refresh() must be called before accessing {method_name}.")
        msg = f"{self.class_name}.{method_name}: "
        msg = f"self.data: {json.dumps(self.data, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        self.properties["border_gateway_count"] = self.data.get("switchRoles", {}).get("border gateway", 0)
        self.properties["leaf_count"] = self.data.get("switchRoles", {}).get("leaf", 0)
        self.properties["spine_count"] = self.data.get("switchRoles", {}).get("spine", 0)
        self.properties["device_count"] = self.leaf_count + self.spine_count + self.border_gateway_count
        
    def refresh(self):
        """
        Refresh the fabric summary info from the controller and
        populate self.data with the result.

        self.data is a dictionary of fabric summary info for one fabric.
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name is required."
            self.ansible_module.fail_json(msg, **self.failed_result)

        try:
            self.endpoints.fabric_name = self.fabric_name
            self.rest_send.path = self.endpoints.fabric_summary.get("path")
            self.rest_send.verb = self.endpoints.fabric_summary.get("verb")
        except ValueError as error:
            msg = "Error retrieving fabric_summary endpoint. "
            msg += f"Detail: {error}"
            self.log.debug(msg)
            self.ansible_module.fail_json(msg, **self.failed_result)

        self.rest_send.commit()
        self.data = copy.deepcopy(self.rest_send.response_current.get("DATA", {}))

        msg = f"self.data: {json.dumps(self.data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.response_current = self.rest_send.response_current
        self.response = self.rest_send.response_current
        self.result_current = self.rest_send.result_current
        self.result = self.rest_send.result_current

        self._update_device_counts()

    def verify_refresh(self, method_name):
        """
        If refresh() has not been called, fail with a message.
        """
        if self.data is None:
            msg = f"refresh() must be called before accessing {method_name}."
            self.ansible_module.fail_json(msg, **self.failed_result)

    @property
    def all_data(self) -> dict:
        """
        Return all fabric details from the controller.
        """
        return self.data

    @property
    def border_gateway_count(self) -> int:
        """
        Return the number of border gateway devices in fabric fabric_name.
        """
        method_name = inspect.stack()[0][3]
        self.verify_refresh(method_name)
        return self.properties["border_gateway_count"]

    @property
    def device_count(self) -> int:
        """
        Return the total number of devices in fabric fabric_name.
        """
        method_name = inspect.stack()[0][3]
        self.verify_refresh(method_name)
        return self.properties["device_count"]

    @property
    def fabric_is_empty(self) -> bool:
        """
        Return True if the fabric is empty.
        """
        method_name = inspect.stack()[0][3]
        self.verify_refresh(method_name)
        if self.device_count == 0:
            return True
        return False

    @property
    def fabric_name(self) -> str:
        """
        Set the fabric_name to query.
        """
        return self.properties.get("fabric_name")

    @fabric_name.setter
    def fabric_name(self, value: str):
        self.properties["fabric_name"] = value

    @property
    def leaf_count(self) -> int:
        """
        Return the number of leaf devices in fabric fabric_name.
        """
        method_name = inspect.stack()[0][3]
        self.verify_refresh(method_name)
        return self.properties["leaf_count"]

    @property
    def spine_count(self) -> int:
        """
        Return the number of spine devices in fabric fabric_name.
        """
        method_name = inspect.stack()[0][3]
        self.verify_refresh(method_name)
        return self.properties["spine_count"]



