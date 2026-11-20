# Copyright (c) 2025 Cisco and/or its affiliates.
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
# pylint: disable=too-many-instance-attributes
"""
Exposes a public class to query fabric-groups on the controller:
- FabricGroupQuery: Query fabric-groups on the controller.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging

from ..common.operation_type import OperationType
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results
from ..fabric_group.fabric_group_details import FabricGroupDetails


class FabricGroupQuery:
    """
    ### Summary
    Retrieve details about fabric groups.

    ### Raises
    -   ``ValueError`` if:
        -   ``fabric_group_details`` is not set.
        -   ``fabric_names`` is not set.
        -   ``rest_send`` is not set.
        -   ``results`` is not set.

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.query import FabricGroupQuery
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend

    params = {"state": "query", "check_mode": False}
    rest_send = RestSend(params)
    results = Results()

    fabric_group_details = FabricDetailsByName()
    fabric_group_details.rest_send = rest_send
    fabric_group_details.results = results # or Results() if you don't want
                                     # fabric_group_details results to be separate
                                     # from FabricGroupQuery results.

    instance = FabricGroupQuery()
    instance.fabric_group_details = fabric_group_details
    instance.fabric_names = ["FABRIC_GROUP_1", "FABRIC_GROUP_2"]
    instance.results = results
    instance.commit()
    results.build_final_result()

    # diff contains a list of dictionaries of fabric group details for each fabric group
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
        self.action = "fabric_group_query"
        self.operation_type: OperationType = OperationType.QUERY

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._fabric_group_names: list[str] = []
        self.fabric_group_details: FabricGroupDetails = FabricGroupDetails()

        # Properties to be set by caller
        self._rest_send: RestSend = RestSend({})
        self._results: Results = Results()

        msg = f"ENTERED {self.class_name}()"
        self.log.debug(msg)

    @property
    def fabric_group_names(self) -> list[str]:
        """
        ### Summary
        -   setter: return the fabric_group_names to query.
        -   getter: set the fabric_group_names to query.

        ### Raises
        -   ``ValueError`` if:
            -   ``value`` is not a list.
            -   ``value`` is an empty list.
            -   ``value`` is not a list of strings.

        """
        return self._fabric_group_names

    @fabric_group_names.setter
    def fabric_group_names(self, value: list[str]) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_names must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise ValueError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_names must be a list of at least one string. "
            msg += f"got {value}."
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "fabric_group_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                raise ValueError(msg)
        self._fabric_group_names = value

    def _validate_commit_parameters(self):
        """
        ### Summary
        -   validate the parameters for commit.

        ### Raises
        -   ``ValueError`` if:
            -   ``fabric_group_details`` is not set.
            -   ``fabric_names`` is not set.
            -   ``rest_send`` is not set.
            -   ``results`` is not set.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if self.fabric_group_details is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_details must be set before calling commit."
            raise ValueError(msg)

        if not self.fabric_group_names:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_names must be set before calling commit."
            raise ValueError(msg)

        # pylint: disable=access-member-before-definition
        if self.results is None:
            # Instantiate Results() to register the failure
            self.results = Results()
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling commit."
            raise ValueError(msg)

    def commit(self) -> None:
        """
        ### Summary
        -   query each of the fabric groups in ``fabric_group_names``.

        ### Raises
        -   ``ValueError`` if:
            -   ``_validate_commit_parameters`` raises ``ValueError``.

        """
        try:
            self._validate_commit_parameters()
        except ValueError as error:
            self.results.add_failed(True)
            if not self.rest_send.params:
                msg = f"{self.class_name}.commit: "
                msg += "rest_send.params must be set before calling commit."
                raise ValueError(f"{error}, {msg}") from error
            if self.rest_send.check_mode in {True, False}:
                self.results.check_mode = self.rest_send.check_mode
            else:
                self.results.check_mode = False
            if self.rest_send.state:
                self.results.state = self.rest_send.state
            else:
                self.results.state = "query"
            self.results.register_task_result()
            raise ValueError(error) from error

        self.fabric_group_details.results = Results()
        self.fabric_group_details.rest_send = self.rest_send

        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state

        msg = f"self.fabric_group_names: {self.fabric_group_names}"
        self.log.debug(msg)
        add_to_diff = {}
        for fabric_group_name in self.fabric_group_names:
            self.fabric_group_details.fabric_group_name = fabric_group_name
            self.fabric_group_details.refresh()
            if fabric_group_name in self.fabric_group_details.all_data:
                add_to_diff[fabric_group_name] = copy.deepcopy(self.fabric_group_details.all_data[fabric_group_name])

        self.results.diff_current = add_to_diff
        self.results.response_current = copy.deepcopy(self.fabric_group_details.results.response_current)
        if not self.results.result_current:
            self.results.result_current = {}
        self.results.result_current = copy.deepcopy(self.fabric_group_details.results.result_current)

        if not add_to_diff:
            msg = f"No fabric details found for {self.fabric_group_names}."
            self.log.debug(msg)
            if not self.results.result_current:
                self.results.result_current = {}
            self.results.result_current["found"] = False
            self.results.result_current["success"] = True
        else:
            msg = f"Found fabric details for {self.fabric_group_names}."
            self.log.debug(msg)

        self.results.register_task_result()

    @property
    def rest_send(self) -> RestSend:
        """
        An instance of the RestSend class.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        if not value.params:
            msg = f"{self.class_name}.rest_send must be set to an "
            msg += "instance of RestSend with params set."
            raise ValueError(msg)
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        An instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        self._results = value
        self._results.action = self.action
        self._results.add_changed(False)
        self._results.operation_type = self.operation_type
