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
"""
Query fabrics.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging
from typing import Literal

from ..common.operation_type import OperationType
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results
from .common_v2 import FabricCommon
from .fabric_details_v3 import FabricDetailsByName


class FabricQuery(FabricCommon):
    """
    # Summary

    Query fabrics.

    ## Raises

    ### ValueError

    - `fabric_names` is not set.
    - `rest_send` is not set.

    ## Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.query import FabricQuery
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.operation_type import OperationType
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results

    params = {"state": "query", "check_mode": False}
    rest_send = RestSend(params)
    results = Results()
    results.operation_type = OperationType.QUERY

    instance = FabricQuery()
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

    def __init__(self) -> None:
        super().__init__()
        self.class_name: str = self.__class__.__name__
        self.action: str = "fabric_query"

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        self._results: Results = Results()
        self._results.operation_type = OperationType.QUERY
        self._rest_send: RestSend = RestSend(params={})

        self._fabric_names: list[str] = []
        self._fabrics_to_query: list[str] = []

        self._fabric_details_by_name: FabricDetailsByName = FabricDetailsByName()
        self._fabric_details_by_name.rest_send = self._rest_send
        self._fabric_details_by_name.results = self._results

        msg = "ENTERED FabricQuery()"
        self.log.debug(msg)

    def _validate_commit_parameters(self) -> None:
        """
        # Summary

        Validate mandatory parameters for commit are set.

        ## Raises

        ### ValueError

        -   `fabric_names` is not set.
        -   `rest_send` is not set.
        """
        method_name: str = inspect.stack()[0][3]

        if not self._fabric_names:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be set before calling commit."
            raise ValueError(msg)

        if not self._rest_send.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit."
            raise ValueError(msg)

    def commit(self) -> None:
        """
        # Summary

        query each of the fabrics in `fabric_names`.

        ## Raises

        ### ValueError

        - `_validate_commit_parameters` raises `ValueError`.

        """
        try:
            self._validate_commit_parameters()
        except ValueError as error:
            self._results.action = self.action
            self._results.add_changed(False)
            self._results.add_failed(True)
            if self._rest_send.params:
                self._results.check_mode = self._rest_send.check_mode
                self._results.state = self._rest_send.state
            else:
                self._results.check_mode = False
                self._results.state = "query"
            self._results.register_task_result()
            raise ValueError(error) from error

        self._fabric_details_by_name.rest_send = self._rest_send
        self._fabric_details_by_name.results = Results()
        self._fabric_details_by_name.results.operation_type = OperationType.QUERY
        self._fabric_details_by_name.refresh()

        self._results.action = self.action
        self._results.check_mode = self._rest_send.check_mode
        self._results.state = self._rest_send.state

        msg = f"self._fabric_names: {self._fabric_names}"
        self.log.debug(msg)
        add_to_diff = {}
        for fabric_name in self._fabric_names:
            if fabric_name in self._fabric_details_by_name.all_data:
                add_to_diff[fabric_name] = copy.deepcopy(
                    self._fabric_details_by_name.all_data[fabric_name]
                )

        self._results.diff_current = add_to_diff
        self._results.response_current = copy.deepcopy(
            self._fabric_details_by_name.results.response_current
        )
        self._results.result_current = copy.deepcopy(
            self._fabric_details_by_name.results.result_current
        )

        if not add_to_diff:
            msg = f"No fabric details found for {self._fabric_names}."
            self.log.debug(msg)
            self._results.result_current["found"] = False
            self._results.result_current["success"] = False
        else:
            msg = f"Found fabric details for {self._fabric_names}."
            self.log.debug(msg)

        self._results.register_task_result()

    @property
    def fabric_names(self) -> list[str]:
        """
        # Summary

        The list of fabric names to query.

        -   setter: return the fabric names
        -   getter: set the fabric_names

        ## Raises

        ### ValueError

        -   `value` is not a list.
        -   `value` is an empty list.
        -   `value` is not a list of strings.

        """
        return self._fabric_names

    @fabric_names.setter
    def fabric_names(self, value: list[str]) -> None:
        method_name: str = inspect.stack()[0][3]

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

    @property
    def rest_send(self) -> RestSend:
        """
        # Summary

        An instance of the RestSend class.

        ## Raises

        -   setter: `TypeError` if the value is not an instance of RestSend.
        -   setter: `ValueError` if RestSend.params is not set.

        ## getter

        Return an instance of the RestSend class.

        ## setter

        Set an instance of the RestSend class.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        method_name: str = inspect.stack()[0][3]
        _class_have: str = ""
        _class_need: Literal["RestSend"] = "RestSend"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        # Summary

        An instance of the Results class.

        ## Raises

        -   setter: `TypeError` if the value is not an instance of Results.

        ## getter

        Return an instance of the Results class.

        ## setter

        Set an instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        method_name: str = inspect.stack()[0][3]
        _class_have: str = ""
        _class_need: Literal["Results"] = "Results"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._results = value
        self._results.action = self.action
        self._results.operation_type = OperationType.QUERY
