# Copyright (c) 2024-2025 Cisco and/or its affiliates.
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
# pylint: disable=too-many-instance-attributes,too-many-public-methods
"""
Exposes public class Results to collect results across tasks.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging


class Results:
    """
    ### Summary
    Collect results across tasks.

    ### Raises
    -   ``TypeError``: if properties are not of the correct type.

    ### Description
    Provides a mechanism to collect results across tasks.  The task classes
    must support this Results class.  Specifically, they must implement the
    following:

    1.  Accept an instantiation of`` Results()``
        -   Typically a class property is used for this
    2.  Populate the ``Results`` instance with the results of the task
        -   Typically done by transferring ``RestSend()``'s responses to the
            ``Results`` instance
    3. Register the results of the task with ``Results``, using:
        -   ``Results.register_task_result()``
        -   Typically done after the task is complete

    ``Results`` should be instantiated in the main Ansible Task class and
    passed to all other task classes.  The task classes should populate the
    ``Results`` instance with the results of the task and then register the
    results with ``Results.register_task_result()``.

    This may be done within a separate class (as in the example below, where
    the ``FabricDelete()`` class is called from the ``TaskDelete()`` class.
    The ``Results`` instance can then be used to build the final result, by
    calling ``Results.build_final_result()``.

    ### Example Usage
    We assume an Ansible module structure as follows:

    -   ``TaskCommon()`` : Common methods used by the various ansible
        state classes.
    -   ``TaskDelete(TaskCommon)`` : Implements the delete state
    -   ``TaskMerge(TaskCommon)``  : Implements the merge state
    -   ``TaskQuery(TaskCommon)``  : Implements the query state
    -   etc...

    In TaskCommon, ``Results`` is instantiated and, hence, is inherited by all
    state classes.:

    ```python
    class TaskCommon:
        def __init__(self):
            self.results = Results()

        @property
        def results(self):
            '''
            An instance of the Results class.
            '''
            return self.properties["results"]

        @results.setter
        def results(self, value):
            self.properties["results"] = value
    ```

    In each of the state classes (TaskDelete, TaskMerge, TaskQuery, etc...)
    a class is instantiated (in the example below, FabricDelete) that
    supports collecting results for the Results instance:

    ```python
    class TaskDelete(TaskCommon):
        def __init__(self, ansible_module):
            super().__init__(ansible_module)
            self.fabric_delete = FabricDelete(self.ansible_module)

        def commit(self):
            '''
            delete the fabric
            '''
            ...
            self.fabric_delete.fabric_names = ["FABRIC_1", "FABRIC_2"]
            self.fabric_delete.results = self.results
            # results.register_task_result() is called within the
            # commit() method of the FabricDelete class.
            self.fabric_delete.commit()
    ```

    Finally, within the main() method of the Ansible module, the final result
    is built by calling Results.build_final_result():

    ```python
    if ansible_module.params["state"] == "deleted":
        task = TaskDelete(ansible_module)
        task.commit()
    elif ansible_module.params["state"] == "merged":
        task = TaskDelete(ansible_module)
        task.commit()
    # etc, for other states...

    # Build the final result
    task.results.build_final_result()

    # Call fail_json() or exit_json() based on the final result
    if True in task.results.failed:
        ansible_module.fail_json(**task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)
    ```

    results.final_result will be a dict with the following structure

    ```json
    {
        "changed": True, # or False
        "failed": True,  # or False
        "diff": {
            [{"diff1": "diff"}, {"diff2": "diff"}, {"etc...": "diff"}],
        }
        "response": {
            [{"response1": "response"}, {"response2": "response"}, {"etc...": "response"}],
        }
        "result": {
            [{"result1": "result"}, {"result2": "result"}, {"etc...": "result"}],
        }
        "metadata": {
            [{"metadata1": "metadata"}, {"metadata2": "metadata"}, {"etc...": "metadata"}],
        }
    }
    ```

    diff, response, and result dicts are per the Ansible DCNM Collection standard output.

    An example of a result dict would be (sequence_number is added by Results):

    ```json
    {
        "found": true,
        "sequence_number": 1,
        "success": true
    }
    ```

    An example of a metadata dict would be (sequence_number is added by Results):


    ```json
    {
        "action": "merge",
        "check_mode": false,
        "state": "merged",
        "sequence_number": 1
    }
    ```

    ``sequence_number`` indicates the order in which the task was registered
    with ``Results``.  It provides a way to correlate the diff, response,
    result, and metadata across all tasks.
    """

    def __init__(self):
        self.class_name: str = self.__class__.__name__

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        msg = f"ENTERED {self.class_name}():"
        self.log.debug(msg)

        self.diff_keys: list = ["deleted", "merged", "query"]
        self.response_keys: list = ["deleted", "merged", "query"]

        # Assign a unique sequence number to each registered task
        self.task_sequence_number: int = 0

        self.final_result: dict = {}
        self._build_properties()

    def _build_properties(self):
        self._action: str = ""
        self._changed: set = set()
        self._check_mode: bool = False
        self._diff: list[dict] = []
        self._diff_current: dict = {}
        self._failed: set = set()
        self._metadata: list[dict] = []
        self._response: list[dict] = []
        self._response_current: dict = {}
        self._response_data: list[dict] = []
        self._result: list[dict] = []
        self._result_current: dict = {}
        self._state: str = ""

    def increment_task_sequence_number(self) -> None:
        """
        Increment a unique task sequence number.
        """
        self.task_sequence_number += 1
        msg = f"self.task_sequence_number: {self.task_sequence_number}"
        self.log.debug(msg)

    def did_anything_change(self) -> bool:  # pylint: disable=too-many-return-statements
        """
        Return True if there were any changes
        Otherwise, return False
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: ENTERED: "
        msg += f"self.action: {self.action}, "
        msg += f"self.state: {self.state}, "
        msg += f"self.result_current: {self.result_current}, "
        msg += f"self.diff: {self.diff}, "
        msg += f"self.failed: {self.failed}"
        self.log.debug(msg)

        something_changed: bool = False
        if self.check_mode is True:
            return False
        if self.action == "query" or self.state == "query":
            return False
        if self.result_current is None:
            return False
        if self.result_current.get("changed", False) is True:
            return True
        if self.result_current.get("changed", True) is False:
            return False
        if "changed" not in self.result_current:
            return False
        for diff in self.diff:
            something_changed = False
            test_diff = copy.deepcopy(diff)
            test_diff.pop("sequence_number", None)
            if len(test_diff) != 0:
                something_changed = True
        msg = f"{self.class_name}.{method_name}: "
        msg += f"something_changed: {something_changed}"
        self.log.debug(msg)
        return something_changed

    def register_task_result(self):
        """
        ### Summary
        Register a task's result.

        ### Description
        1.  Append result_current, response_current, diff_current and
            metadata_current their respective lists (result, response, diff,
            and metadata)
        2.  Set self.changed based on current_diff.
            If current_diff is empty, it is assumed that no changes were made
            and self.changed is set to False.  Else, self.changed is set to True.
        3.  Set self.failed based on current_result.  If current_result["success"]
            is True, self.failed is set to False.  Else, self.failed is set to True.
        4.  Set self.metadata based on current_metadata.

        - self.response  : list of controller responses
        - self.result    : list of results returned by the handler
        - self.diff      : list of diffs
        - self.metadata  : list of metadata
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"ENTERED: self.action: {self.action}, "
        msg += f"self.result_current: {self.result_current}"
        self.log.debug(msg)

        self.increment_task_sequence_number()
        self.metadata = self.metadata_current
        self.response = self.response_current
        self.result = self.result_current
        self.diff = self.diff_current

        if self.did_anything_change() is False:
            self.changed = False
        else:
            self.changed = True
        if self.result_current.get("success") is True:
            self.failed = False
        elif self.result_current.get("success") is False:
            self.failed = True
        else:
            msg = f"{self.class_name}.{method_name}: "
            msg += "self.result_current['success'] is not a boolean. "
            msg += f"self.result_current: {self.result_current}. "
            msg += "Setting self.failed to False."
            self.log.debug(msg)
            self.failed = False

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff: {json.dumps(self.diff, indent=4, sort_keys=True)}, "
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.metadata: {json.dumps(self.metadata, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.response: {json.dumps(self.response, indent=4, sort_keys=True)}, "
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.result: {json.dumps(self.result, indent=4, sort_keys=True)}, "
        self.log.debug(msg)

    def build_final_result(self):
        """
        ### Summary
        Build the final result.

        ### Description
        The final result consists of the following:
        ```json
        {
            "changed": True, # or False
            "failed": True,
            "diff": {
                [<list of dict containing changes>],
            },
            "response": {
                [<list of dict containing controller responses>],
            },
            "result": {
                [<list of dict containing results (from handle_response() functions)>],
            },
            "metadata": {
                [<list of dict containing metadata>],
            }
        ```
        """
        msg = f"self.changed: {self.changed}, "
        msg = f"self.failed: {self.failed}, "
        self.log.debug(msg)

        if True in self.failed:  # pylint: disable=unsupported-membership-test
            self.final_result["failed"] = True
        else:
            self.final_result["failed"] = False

        if True in self.changed:  # pylint: disable=unsupported-membership-test
            self.final_result["changed"] = True
        else:
            self.final_result["changed"] = False
        self.final_result["diff"] = self.diff
        self.final_result["response"] = self.response
        self.final_result["result"] = self.result
        self.final_result["metadata"] = self.metadata

    def add_to_failed(self, value: bool) -> None:
        """
        Add a boolean value to the failed set.
        """
        if not isinstance(value, bool):
            msg = f"{self.class_name}.add_to_failed: "
            msg += f"instance.add_to_failed must be a bool. Got {value}"
            raise ValueError(msg)
        self._failed.add(value)

    @property
    def failed_result(self) -> dict:
        """
        return a result for a failed task with no changes
        """
        result: dict = {}
        result["changed"] = False
        result["failed"] = True
        result["diff"] = [{}]
        result["response"] = [{}]
        result["result"] = [{}]
        return result

    @property
    def ok_result(self) -> dict:
        """
        return a result for a successful task with no changes
        """
        result: dict = {}
        result["changed"] = False
        result["failed"] = False
        result["diff"] = [{}]
        result["response"] = [{}]
        result["result"] = [{}]
        return result

    @property
    def action(self):
        """
        ### Summary
        Added to results to indicate the action that was taken

        ### Raises
        -   ``TypeError``: if value is not a string
        """
        return self._action

    @action.setter
    def action(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.{method_name} must be a string. "
            msg += f"Got {value}."
            raise TypeError(msg)
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value: {value}"
        self.log.debug(msg)
        self._action = value

    @property
    def changed(self) -> set:
        """
        ### Summary
        - A ``set()`` containing boolean values indicating whether
        anything changed.
        - The setter adds a boolean value to the set.
        - The getter returns the set.

        ### Raises
        -   setter: ``TypeError``: if value is not a bool

        ### Returns
        -   A set() of Boolean values indicating whether any tasks changed
        """
        return self._changed

    @changed.setter
    def changed(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.changed must be a bool. Got {value}"
            raise TypeError(msg)
        self._changed.add(value)

    @property
    def check_mode(self) -> bool:
        """
        ### Summary
        - A boolean indicating whether Ansible check_mode is enabled.
        - ``True`` if check_mode is enabled, ``False`` otherwise.

        ### Raises
        -   ``TypeError``: if value is not a bool
        """
        return self._check_mode

    @check_mode.setter
    def check_mode(self, value: bool) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.{method_name} must be a bool. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self._check_mode = value

    @property
    def diff(self) -> list[dict]:
        """
        ### Summary
        - A list of dicts representing the changes made.
        - The setter appends a dict to the list.
        - The getter returns the list.

        ### Raises
        -   setter: ``TypeError``: if value is not a dict
        """
        return self._diff

    @diff.setter
    def diff(self, value: dict):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.diff must be a dict. Got {value}"
            raise TypeError(msg)
        value["sequence_number"] = self.task_sequence_number
        self._diff.append(copy.deepcopy(value))

    @property
    def diff_current(self) -> dict:
        """
        ### Summary
        -   getter: Return the current diff
        -   setter: Set the current diff

        ### Raises
        -   setter: ``TypeError`` if value is not a dict.
        """
        value = self._diff_current
        value["sequence_number"] = self.task_sequence_number
        return value

    @diff_current.setter
    def diff_current(self, value: dict):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.diff_current must be a dict. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self._diff_current = value

    @property
    def failed(self) -> set[bool]:
        """
        ### Summary
        - A set() of Boolean values indicating whether any tasks failed
        - If the set contains True, at least one task failed.
        - If the set contains only False all tasks succeeded.

        ### Raises
        - ``TypeError`` if value is not a bool.
        """
        return self._failed

    @failed.setter
    def failed(self, value: bool) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            # Setting failed, itself failed(!)
            # Add True to failed to indicate this.
            self._failed.add(True)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.failed must be a bool. Got {value}"
            raise TypeError(msg)
        self.add_to_failed(value)

    @property
    def metadata(self) -> list[dict]:
        """
        ### Summary
        - List of dicts representing the metadata (if any) for each diff.
        -   getter: Return the metadata.
        -   setter: Append value to the metadata list.

        ### Raises
        -   setter: ``TypeError`` if value is not a dict.
        """
        return self._metadata

    @metadata.setter
    def metadata(self, value: dict):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.metadata must be a dict. Got {value}"
            raise TypeError(msg)
        value["sequence_number"] = self.task_sequence_number
        self._metadata.append(copy.deepcopy(value))

    @property
    def metadata_current(self):
        """
        ### Summary
        -   getter: Return the current metadata which is comprised of the
            properties action, check_mode, and state.

        ### Raises
        None
        """
        value = {}
        value["action"] = self.action
        value["check_mode"] = self.check_mode
        value["state"] = self.state
        value["sequence_number"] = self.task_sequence_number
        return value

    @property
    def response_current(self) -> dict:
        """
        ### Summary
        - Return a ``dict`` containing the current response from the controller.
        ``instance.commit()`` must be called first.
        -   getter: Return the current response.
        -   setter: Set the current response.

        ### Raises
        -   setter: ``TypeError`` if value is not a dict.
        """
        value = self._response_current
        value["sequence_number"] = self.task_sequence_number
        return value

    @response_current.setter
    def response_current(self, value: dict):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.response_current must be a dict. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self._response_current = value

    @property
    def response(self) -> list[dict]:
        """
        ### Summary
        -   A ``list`` of ``dict``, where each ``dict`` contains a response
            from the controller.
        -   getter: Return the response list.
        -   setter: Append ``dict`` to the response list.

        ### Raises
        - setter: ``TypeError``: if value is not a dict.
        """
        return self._response

    @response.setter
    def response(self, value: dict):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.response must be a dict. "
            msg += f"Got {value}."
            raise TypeError(msg)
        value["sequence_number"] = self.task_sequence_number
        self._response.append(copy.deepcopy(value))

    @property
    def response_data(self) -> list[dict]:
        """
        ### Summary
        -   getter: Return the contents of the DATA key within
            ``current_response``.
        -   setter: set ``response_data`` to the value passed in
            which should be the contents of the DATA key within
            ``current_response``.

        ### Raises
        None
        """
        return self._response_data

    @response_data.setter
    def response_data(self, value: dict):
        self._response_data.append(value)

    @property
    def result(self) -> list[dict]:
        """
        ### Summary
        -   A ``list`` of ``dict``, where each ``dict`` contains a result.
        -   getter: Return the result list.
        -   setter: Append ``dict`` to the result list.

        ### Raises
        -   setter: ``TypeError`` if value is not a dict
        """
        return self._result

    @result.setter
    def result(self, value: dict):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.result must be a dict. "
            msg += f"Got {value}."
            raise TypeError(msg)
        value["sequence_number"] = self.task_sequence_number
        self._result.append(copy.deepcopy(value))

    @property
    def result_current(self):
        """
        ### Summary
        -   The current result.
        -   getter: Return the current result.
        -   setter: Set the current result.

        ### Raises
        -   setter: ``TypeError`` if value is not a dict
        """
        value = self._result_current
        value["sequence_number"] = self.task_sequence_number
        return value

    @result_current.setter
    def result_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.result_current must be a dict. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self._result_current = value

    @property
    def state(self):
        """
        ### Summary
        -   The Ansible state
        -   getter: Return the state.
        -   setter: Set the state.

        ### Raises
        -   setter: ``TypeError`` if value is not a string
        """
        return self._state

    @state.setter
    def state(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.{method_name} must be a string. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self._state = value
