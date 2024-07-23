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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon


class FabricQuery(FabricCommon):
    """
    ### Summary
    Query fabrics.

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.query import FabricQuery
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results

    params = {"state": "query", "check_mode": False}
    rest_send = RestSend(params)
    results = Results()

    fabric_details = FabricDetailsByName()
    fabric_details.rest_send = rest_send
    fabric_details.results = results # or Results() if you don't want
                                     # fabric_details results to be separate
                                     # from FabricQuery results.

    instance = FabricQuery()
    instance.fabric_details = fabric_details
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
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.action = "fabric_query"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._fabrics_to_query = []
        self._fabric_names = None

        msg = "ENTERED FabricQuery()"
        self.log.debug(msg)

    @property
    def fabric_names(self):
        """
        - setter: return the fabric names
        - getter: set the fable_names
        - getter: raise ``ValueError`` if ``value`` is not a ``list``
        - getter: raise ``ValueError`` if ``value`` is an empty list
        - getter: raise ``ValueError`` if ``value`` is not a list of strings

        """
        return self._fabric_names

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
        self._fabric_names = value

    def _validate_commit_parameters(self):
        """
        - validate the parameters for commit
        - raise ``ValueError`` if ``fabric_names`` is not set
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if self.fabric_details is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_details must be set before calling commit."
            raise ValueError(msg)

        if self.fabric_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be set before calling commit."
            raise ValueError(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit."
            raise ValueError(msg)

        if self.results is None:
            # Instantiate Results() to register the failure
            self.results = Results()
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling commit."
            raise ValueError(msg)

    def commit(self):
        """
        - query each of the fabrics in self.fabric_names
        - raise ``ValueError`` if ``fabric_names`` is not set
        - raise ``ValueError`` if ``fabric_details`` is not set

        """
        try:
            self._validate_commit_parameters()
        except ValueError as error:
            self.results.action = self.action
            self.results.changed = False
            self.results.failed = True
            if self.rest_send is not None:
                self.results.check_mode = self.rest_send.check_mode
                self.results.state = self.rest_send.state
            else:
                self.results.check_mode = False
                self.results.state = "query"
            self.results.register_task_result()
            raise ValueError(error) from error

        self.fabric_details.refresh()

        self.results.action = self.action
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state

        msg = f"self.fabric_names: {self.fabric_names}"
        self.log.debug(msg)
        add_to_diff = {}
        for fabric_name in self.fabric_names:
            if fabric_name in self.fabric_details.all_data:
                add_to_diff[fabric_name] = copy.deepcopy(
                    self.fabric_details.all_data[fabric_name]
                )

        self.results.diff_current = add_to_diff
        self.results.response_current = copy.deepcopy(
            self.fabric_details.results.response_current
        )
        self.results.result_current = copy.deepcopy(
            self.fabric_details.results.result_current
        )
        self.results.register_task_result()
