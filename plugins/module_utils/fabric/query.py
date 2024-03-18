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

from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName


class FabricQuery(FabricCommon):
    """
    Query fabrics

    Usage:
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.query import FabricQuery
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results

    results = Results()
    instance = FabricQuery(ansible_module)
    instance.fabric_names = ["FABRIC_1", "FABRIC_2"]
    instance.results = results
    instance.commit()
    results.build_final_result()

    # diff contains a dictionary of fabric details for each fabric
    # in instance.fabric_names
    diff = results.diff
    # result contains the result(s) of the query request
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

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED FabricQuery(): "
        msg += f"state: {self.state}"
        self.log.debug(msg)

        self._fabrics_to_query = []
        self._build_properties()
        self._fabric_details = FabricDetailsByName(self.ansible_module)

        self.action = "query"
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

    def commit(self):
        """
        query each of the fabrics in self.fabric_names
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        self._fabric_details.refresh()

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state

        if self._fabric_details.result_current.get("success") is False:
            self.results.diff_current = {}
            self.results.response_current = copy.deepcopy(self._fabric_details.response_current)
            self.results.result_current = copy.deepcopy(self._fabric_details.result_current)
            self.results.register_task_result()
            return

        for fabric_name in self.fabric_names:
            if fabric_name not in self._fabric_details.all_data:
                continue
            self.results.diff_current = copy.deepcopy(self._fabric_details.all_data[fabric_name])
            self.results.response_current = copy.deepcopy(self._fabric_details.response_current)
            self.results.result_current = copy.deepcopy(self._fabric_details.result_current)
            self.results.register_task_result()
